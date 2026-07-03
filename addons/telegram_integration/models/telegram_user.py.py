# -*- coding: utf-8 -*-
"""
Telegram Bot User Model
Tracks users who interact with the bot
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class TelegramBotUser(models.Model):
    _name = 'telegram.bot.user'
    _description = 'Telegram Bot User'
    _rec_name = 'first_name'
    _order = 'last_interaction desc'

    # Telegram Information
    telegram_user_id = fields.Char(
        string='Telegram User ID',
        required=True,
        index=True,
        help='Unique Telegram user identifier'
    )
    
    first_name = fields.Char(
        string='First Name',
        required=True
    )
    
    last_name = fields.Char(
        string='Last Name'
    )
    
    username = fields.Char(
        string='Telegram Username',
        help='Telegram username (without @)'
    )
    
    language_code = fields.Char(
        string='Language',
        help='User language code (e.g., en, id)'
    )
    
    is_bot = fields.Boolean(
        string='Is Bot',
        default=False
    )
    
    # Chat Information
    chat_id = fields.Char(
        string='Chat ID',
        required=True,
        index=True,
        help='Telegram chat identifier'
    )
    
    chat_type = fields.Selection([
        ('private', 'Private Chat'),
        ('group', 'Group Chat'),
        ('supergroup', 'Supergroup'),
        ('channel', 'Channel'),
    ], string='Chat Type', default='private')
    
    # Status
    is_active = fields.Boolean(
        string='Active',
        default=True
    )
    
    is_blocked = fields.Boolean(
        string='Blocked',
        default=False,
        help='User has been blocked from using the bot'
    )
    
    is_admin = fields.Boolean(
        string='Admin',
        default=False,
        help='User has admin privileges'
    )
    
    # Activity Tracking
    first_interaction = fields.Datetime(
        string='First Interaction',
        readonly=True
    )
    
    last_interaction = fields.Datetime(
        string='Last Interaction',
        readonly=True
    )
    
    total_messages = fields.Integer(
        string='Total Messages',
        default=0,
        readonly=True
    )
    
    messages_today = fields.Integer(
        string='Messages Today',
        compute='_compute_messages_today',
        store=False
    )
    
    # Odoo Relations
    bot_id = fields.Many2one(
        'telegram.bot',
        string='Bot',
        required=True,
        ondelete='cascade'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Linked Odoo partner/customer'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Odoo User',
        help='Linked Odoo user account'
    )
    
    message_ids = fields.One2many(
        'telegram.message',
        'user_id',
        string='Messages',
        readonly=True
    )
    
    # Preferences
    notification_enabled = fields.Boolean(
        string='Notifications Enabled',
        default=True
    )
    
    notification_order_update = fields.Boolean(
        string='Order Updates',
        default=True
    )
    
    notification_invoice = fields.Boolean(
        string='Invoice Notifications',
        default=True
    )
    
    notification_promotion = fields.Boolean(
        string='Promotional Messages',
        default=True
    )
    
    # Additional Data
    extra_data = fields.Text(
        string='Additional Data',
        help='JSON data with additional user information'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Internal notes about this user'
    )
    
    # Metadata
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='bot_id.company_id',
        store=True
    )

    # ==================== Constraints ====================
    
    _sql_constraints = [
        ('unique_telegram_user_per_bot', 
         'UNIQUE(bot_id, telegram_user_id)',
         'User already exists for this bot!'),
        ('unique_chat_per_bot',
         'UNIQUE(bot_id, chat_id)',
         'Chat ID already exists for this bot!'),
    ]

    @api.constrains('telegram_user_id')
    def _check_telegram_user_id(self):
        """Validate Telegram user ID"""
        for user in self:
            if user.telegram_user_id and not user.telegram_user_id.isdigit():
                raise ValidationError(_('Telegram User ID must be numeric.'))

    # ==================== Computed Fields ====================
    
    @api.depends('message_ids')
    def _compute_messages_today(self):
        """Calculate messages sent today"""
        today = fields.Datetime.now().strftime('%Y-%m-%d')
        for user in self:
            user.messages_today = len(user.message_ids.filtered(
                lambda m: m.create_date and 
                         m.create_date.strftime('%Y-%m-%d') == today
            ))

    # ==================== CRUD Methods ====================
    
    @api.model
    def create(self, vals):
        """Create user with initial interaction timestamp"""
        if not vals.get('first_interaction'):
            vals['first_interaction'] = fields.Datetime.now()
        if not vals.get('last_interaction'):
            vals['last_interaction'] = fields.Datetime.now()
        
        user = super(TelegramBotUser, self).create(vals)
        
        # Auto-link to partner if username matches email
        if user.username and not user.partner_id:
            user._auto_link_partner()
        
        return user

    def write(self, vals):
        """Update last interaction timestamp"""
        if any(f in vals for f in ['message_ids']):
            vals['last_interaction'] = fields.Datetime.now()
        
        return super(TelegramBotUser, self).write(vals)

    # ==================== Action Methods ====================
    
    def action_send_message(self):
        """Open wizard to send message to user"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send Message'),
            'res_model': 'telegram.send.message.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bot_id': self.bot_id.id,
                'default_recipient_type': 'specific',
                'default_chat_id': self.chat_id,
                'default_user_ids': [(6, 0, [self.id])],
            }
        }

    def action_toggle_block(self):
        """Toggle user block status"""
        for user in self:
            user.is_blocked = not user.is_blocked
            status = 'blocked' if user.is_blocked else 'unblocked'
            user.message_post(body=_('User %s') % status)

    def action_view_messages(self):
        """View user's message history"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Messages'),
            'res_model': 'telegram.message',
            'view_mode': 'tree,form',
            'domain': [('user_id', '=', self.id)],
            'context': {'search_default_user_id': self.id},
        }

    def action_link_to_partner(self):
        """Link user to existing partner"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Link to Partner'),
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [
                '|',
                ('name', 'ilike', self.first_name),
                ('email', 'ilike', self.username or ''),
            ],
            'context': {
                'default_telegram_user_id': self.telegram_user_id,
                'default_telegram_username': self.username,
            }
        }

    # ==================== Helper Methods ====================
    
    def _auto_link_partner(self):
        """Auto-link user to partner based on username"""
        self.ensure_one()
        
        if self.username:
            # Search by email-like username
            email = f"{self.username}@telegram.com"
            partner = self.env['res.partner'].search([
                ('email', '=', email)
            ], limit=1)
            
            if partner:
                self.partner_id = partner.id
                self.message_post(body=_('Auto-linked to partner %s') % partner.name)
                return True
        
        return False

    def _update_activity(self):
        """Update user activity timestamp"""
        self.last_interaction = fields.Datetime.now()
        self.total_messages += 1

    def _get_full_name(self):
        """Get user's full name"""
        self.ensure_one()
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    def _get_mention(self):
        """Get user mention for messages"""
        self.ensure_one()
        if self.username:
            return f"@{self.username}"
        return self._get_full_name()