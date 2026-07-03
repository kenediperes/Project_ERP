# -*- coding: utf-8 -*-
"""
Telegram Bot Model
Core bot configuration and management
"""

import json
import logging
import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class TelegramBot(models.Model):
    _name = 'telegram.bot'
    _description = 'Telegram Bot Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char(
        string='Bot Name',
        required=True,
        tracking=True,
        help='Name of your Telegram bot'
    )
    
    bot_token = fields.Char(
        string='Bot Token',
        required=True,
        copy=False,
        groups='base.group_system',
        help='Bot token obtained from @BotFather on Telegram'
    )
    
    bot_username = fields.Char(
        string='Bot Username',
        compute='_compute_bot_username',
        store=True,
        help='Username of the bot (without @)'
    )
    
    description = fields.Text(
        string='Description',
        help='Description of the bot functionality'
    )
    
    # Status
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Enable or disable the bot'
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('configured', 'Configured'),
        ('running', 'Running'),
        ('error', 'Error'),
        ('stopped', 'Stopped'),
    ], string='Status', default='draft', tracking=True, required=True)
    
    # Webhook Configuration
    webhook_url = fields.Char(
        string='Webhook URL',
        compute='_compute_webhook_url',
        store=True,
        help='URL where Telegram will send updates'
    )
    
    webhook_set = fields.Boolean(
        string='Webhook Configured',
        default=False,
        help='Indicates if webhook is properly configured'
    )
    
    last_webhook_check = fields.Datetime(
        string='Last Webhook Check',
        help='Last time the webhook status was checked'
    )
    
    # Bot Settings
    allowed_updates = fields.Selection([
        ('message', 'Messages Only'),
        ('all', 'All Updates'),
        ('custom', 'Custom'),
    ], string='Allowed Updates', default='message',
       help='Type of updates the bot will receive')
    
    custom_updates = fields.Text(
        string='Custom Updates',
        help='JSON array of allowed update types',
        default='["message", "callback_query"]'
    )
    
    max_connections = fields.Integer(
        string='Max Connections',
        default=40,
        help='Maximum number of simultaneous HTTPS connections'
    )
    
    # Security
    secret_token = fields.Char(
        string='Secret Token',
        copy=False,
        groups='base.group_system',
        help='Secret token for webhook security'
    )
    
    use_secret_token = fields.Boolean(
        string='Use Secret Token',
        default=False,
        help='Enable secret token verification for webhook'
    )
    
    # Statistics
    total_users = fields.Integer(
        string='Total Users',
        compute='_compute_statistics',
        store=True,
        help='Total number of users who have interacted with the bot'
    )
    
    total_messages = fields.Integer(
        string='Total Messages',
        compute='_compute_statistics',
        store=True,
        help='Total number of messages processed'
    )
    
    messages_today = fields.Integer(
        string='Messages Today',
        compute='_compute_statistics',
        store=False,
        help='Number of messages processed today'
    )
    
    active_users_today = fields.Integer(
        string='Active Users Today',
        compute='_compute_statistics',
        store=False,
        help='Number of active users today'
    )
    
    success_rate = fields.Float(
        string='Success Rate',
        compute='_compute_statistics',
        store=False,
        help='Percentage of successfully delivered messages'
    )
    
    last_activity = fields.Datetime(
        string='Last Activity',
        compute='_compute_statistics',
        store=True,
        help='Last time the bot received or sent a message'
    )
    
    # Relations
    command_ids = fields.One2many(
        'telegram.command',
        'bot_id',
        string='Commands',
        help='Bot commands configuration'
    )
    
    user_ids = fields.One2many(
        'telegram.bot.user',
        'bot_id',
        string='Users',
        help='Users who have interacted with the bot'
    )
    
    message_ids = fields.One2many(
        'telegram.message',
        'bot_id',
        string='Messages',
        help='Message history'
    )
    
    template_ids = fields.One2many(
        'telegram.template',
        'bot_id',
        string='Message Templates',
        help='Predefined message templates'
    )
    
    # Owner
    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # ==================== Computed Fields ====================
    
    @api.depends('bot_token')
    def _compute_bot_username(self):
        """Extract bot username from token or API"""
        for bot in self:
            if bot.bot_token:
                try:
                    response = requests.get(
                        f'https://api.telegram.org/bot{bot.bot_token}/getMe',
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('ok'):
                            bot.bot_username = data['result']['username']
                        else:
                            bot.bot_username = False
                    else:
                        bot.bot_username = False
                except Exception as e:
                    _logger.error(f"Error getting bot username: {e}")
                    bot.bot_username = False
            else:
                bot.bot_username = False

    @api.depends('bot_token')
    def _compute_webhook_url(self):
        """Compute webhook URL based on system base URL"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for bot in self:
            if base_url:
                bot.webhook_url = f'{base_url}/telegram/webhook/{bot.id}'
            else:
                bot.webhook_url = False

    @api.depends('user_ids', 'message_ids')
    def _compute_statistics(self):
        """Compute bot statistics"""
        for bot in self:
            # Total users
            bot.total_users = len(bot.user_ids)
            
            # Total messages
            bot.total_messages = len(bot.message_ids)
            
            # Messages today
            today = fields.Datetime.now().strftime('%Y-%m-%d')
            bot.messages_today = len(bot.message_ids.filtered(
                lambda m: m.create_date and m.create_date.strftime('%Y-%m-%d') == today
            ))
            
            # Active users today
            bot.active_users_today = len(bot.user_ids.filtered(
                lambda u: u.last_interaction and 
                         u.last_interaction.strftime('%Y-%m-%d') == today
            ))
            
            # Success rate
            total_outgoing = len(bot.message_ids.filtered(
                lambda m: m.direction == 'outgoing'
            ))
            if total_outgoing > 0:
                successful = len(bot.message_ids.filtered(
                    lambda m: m.direction == 'outgoing' and 
                             m.state in ['sent', 'delivered']
                ))
                bot.success_rate = round((successful / total_outgoing) * 100, 2)
            else:
                bot.success_rate = 100.0
            
            # Last activity
            if bot.message_ids:
                bot.last_activity = max(bot.message_ids.mapped('create_date'))
            else:
                bot.last_activity = False

    # ==================== Constraints ====================
    
    _sql_constraints = [
        ('unique_bot_token', 'UNIQUE(bot_token)', 
         'Bot token must be unique! Each bot should have a unique token.'),
    ]

    @api.constrains('bot_token')
    def _check_bot_token(self):
        """Validate bot token format and connectivity"""
        for bot in self:
            if not bot.bot_token:
                continue
            
            # Basic format check
            if ':' not in bot.bot_token:
                raise ValidationError(_('Invalid bot token format. '
                                      'Token should contain a colon (:).'))
            
            # Test connectivity if token changed
            if bot.state == 'draft' or bot._origin.bot_token != bot.bot_token:
                try:
                    response = requests.get(
                        f'https://api.telegram.org/bot{bot.bot_token}/getMe',
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('ok'):
                            bot.state = 'configured'
                        else:
                            raise ValidationError(_(
                                'Invalid bot token: %s' % data.get('description', 'Unknown error')
                            ))
                    else:
                        raise ValidationError(_(
                            'Cannot connect to Telegram API. Please check your internet connection.'
                        ))
                except requests.exceptions.RequestException as e:
                    raise ValidationError(_(
                        'Cannot connect to Telegram API: %s' % str(e)
                    ))

    # ==================== CRUD Methods ====================
    
    @api.model
    def create(self, vals):
        """Create bot and set webhook"""
        bot = super(TelegramBot, self).create(vals)
        if bot.is_active:
            bot.action_start()
        return bot

    def write(self, vals):
        """Update bot and manage webhook"""
        result = super(TelegramBot, self).write(vals)
        
        if 'is_active' in vals:
            for bot in self:
                if vals['is_active']:
                    bot.action_start()
                else:
                    bot.action_stop()
        
        if 'bot_token' in vals:
            for bot in self:
                bot.webhook_set = False
                if bot.is_active:
                    bot.set_webhook()
        
        return result

    def unlink(self):
        """Remove webhook before deleting bot"""
        for bot in self:
            bot.delete_webhook()
        return super(TelegramBot, self).unlink()

    # ==================== Action Methods ====================
    
    def action_start(self):
        """Start the bot"""
        self.ensure_one()
        if not self.bot_token:
            raise UserError(_('Please configure the bot token first.'))
        
        self.set_webhook()
        self.state = 'running'
        self.message_post(body=_('Bot started successfully. Webhook configured.'))
        
        # Notify admin
        self._notify_status_change('started')

    def action_stop(self):
        """Stop the bot"""
        self.ensure_one()
        self.delete_webhook()
        self.state = 'stopped'
        self.message_post(body=_('Bot stopped. Webhook removed.'))

    def action_restart(self):
        """Restart the bot"""
        self.ensure_one()
        self.action_stop()
        self.action_start()
        self.message_post(body=_('Bot restarted.'))

    def action_test_connection(self):
        """Test bot connectivity"""
        self.ensure_one()
        try:
            response = requests.get(
                f'https://api.telegram.org/bot{self.bot_token}/getMe',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data['result']
                    message = _(
                        'Connection successful!\n'
                        'Bot: @%s\n'
                        'Name: %s\n'
                        'ID: %s'
                    ) % (bot_info['username'], bot_info['first_name'], bot_info['id'])
                    self.message_post(body=message)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Success'),
                            'message': message,
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    raise UserError(_('Error: %s') % data.get('description'))
            else:
                raise UserError(_('Cannot connect to Telegram API'))
        except Exception as e:
            raise UserError(_('Connection test failed: %s') % str(e))

    # ==================== Webhook Methods ====================
    
    def set_webhook(self):
        """Set webhook for the bot"""
        self.ensure_one()
        
        if not self.webhook_url:
            raise UserError(_('Cannot set webhook: Webhook URL is not configured.'))
        
        webhook_data = {
            'url': self.webhook_url,
            'max_connections': self.max_connections,
        }
        
        # Add allowed updates
        if self.allowed_updates == 'custom':
            try:
                webhook_data['allowed_updates'] = json.loads(self.custom_updates)
            except json.JSONDecodeError:
                webhook_data['allowed_updates'] = ["message", "callback_query"]
        elif self.allowed_updates == 'all':
            webhook_data['allowed_updates'] = [
                "message", "edited_message", "channel_post",
                "edited_channel_post", "callback_query", "inline_query",
                "chosen_inline_result", "shipping_query", "pre_checkout_query"
            ]
        
        # Add secret token if enabled
        if self.use_secret_token and self.secret_token:
            webhook_data['secret_token'] = self.secret_token
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/setWebhook',
                json=webhook_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    self.webhook_set = True
                    self.last_webhook_check = fields.Datetime.now()
                    _logger.info(f'Webhook set successfully for bot {self.name}')
                    self.message_post(body=_(
                        'Webhook configured successfully.\n'
                        'URL: %s\n'
                        'Max Connections: %s'
                    ) % (self.webhook_url, self.max_connections))
                    return True
                else:
                    error_msg = data.get('description', 'Unknown error')
                    _logger.error(f'Failed to set webhook: {error_msg}')
                    self.message_post(body=_(
                        'Failed to configure webhook: %s'
                    ) % error_msg)
                    return False
            else:
                _logger.error(f'Telegram API error: {response.status_code}')
                return False
                
        except Exception as e:
            _logger.error(f'Exception setting webhook: {e}')
            self.message_post(body=_('Error configuring webhook: %s') % str(e))
            return False

    def delete_webhook(self):
        """Remove webhook for the bot"""
        self.ensure_one()
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/deleteWebhook',
                json={'drop_pending_updates': True},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    self.webhook_set = False
                    _logger.info(f'Webhook removed for bot {self.name}')
                    return True
            
            return False
            
        except Exception as e:
            _logger.error(f'Error deleting webhook: {e}')
            return False

    def get_webhook_info(self):
        """Get current webhook information"""
        self.ensure_one()
        
        try:
            response = requests.get(
                f'https://api.telegram.org/bot{self.bot_token}/getWebhookInfo',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data['result']
            
            return {}
            
        except Exception as e:
            _logger.error(f'Error getting webhook info: {e}')
            return {}

    # ==================== Messaging Methods ====================
    
    def send_message(self, chat_id, text, parse_mode='HTML', 
                    reply_markup=None, disable_notification=False):
        """
        Send message via Telegram API
        
        Args:
            chat_id: Telegram chat ID
            text: Message text
            parse_mode: Parse mode (HTML, Markdown, None)
            reply_markup: Inline keyboard markup
            disable_notification: Send silently
            
        Returns:
            dict: API response
        """
        self.ensure_one()
        
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_notification': disable_notification,
        }
        
        if reply_markup:
            payload['reply_markup'] = json.dumps(reply_markup)
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/sendMessage',
                json=payload,
                timeout=30
            )
            
            return response.json()
            
        except Exception as e:
            _logger.error(f'Error sending message: {e}')
            return {'ok': False, 'description': str(e)}

    def send_photo(self, chat_id, photo, caption=None, parse_mode='HTML'):
        """Send photo via Telegram"""
        self.ensure_one()
        
        payload = {
            'chat_id': chat_id,
            'photo': photo,
            'parse_mode': parse_mode,
        }
        
        if caption:
            payload['caption'] = caption
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/sendPhoto',
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            _logger.error(f'Error sending photo: {e}')
            return {'ok': False, 'description': str(e)}

    def send_document(self, chat_id, document, caption=None):
        """Send document via Telegram"""
        self.ensure_one()
        
        payload = {
            'chat_id': chat_id,
            'document': document,
        }
        
        if caption:
            payload['caption'] = caption
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/sendDocument',
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            _logger.error(f'Error sending document: {e}')
            return {'ok': False, 'description': str(e)}

    def answer_callback_query(self, callback_query_id, text=None, show_alert=False):
        """Answer callback query"""
        self.ensure_one()
        
        payload = {
            'callback_query_id': callback_query_id,
            'show_alert': show_alert,
        }
        
        if text:
            payload['text'] = text
        
        try:
            response = requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery',
                json=payload,
                timeout=10
            )
            return response.json()
        except Exception as e:
            _logger.error(f'Error answering callback: {e}')
            return {'ok': False, 'description': str(e)}

    # ==================== Helper Methods ====================
    
    def _notify_status_change(self, status):
        """Notify relevant users about status change"""
        notification_template = self.env.ref(
            'telegram_integration.telegram_bot_status_notification',
            raise_if_not_found=False
        )
        
        if notification_template and self.user_id:
            notification_template.send_mail(
                self.id,
                force_send=True,
                email_values={'recipient_ids': [(4, self.user_id.partner_id.id)]}
            )

    def _get_commands_for_botfather(self):
        """Get commands list formatted for BotFather"""
        commands = []
        for cmd in self.command_ids.filtered(lambda c: c.is_active):
            commands.append(f"{cmd.name} - {cmd.description}")
        return '\n'.join(commands)

    def _generate_secret_token(self):
        """Generate a secure secret token"""
        import secrets
        return secrets.token_urlsafe(32)