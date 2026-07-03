# -*- coding: utf-8 -*-
"""
Telegram Message Model
Logs all messages sent and received via Telegram
"""

import json
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class TelegramMessage(models.Model):
    _name = 'telegram.message'
    _description = 'Telegram Message'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    _rec_name = 'message_text'

    # Basic Information
    telegram_message_id = fields.Char(
        string='Telegram Message ID',
        index=True,
        help='Message ID from Telegram API'
    )
    
    message_text = fields.Text(
        string='Message',
        help='Message content'
    )
    
    message_type = fields.Selection([
        ('text', 'Text'),
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('audio', 'Audio'),
        ('video', 'Video'),
        ('voice', 'Voice'),
        ('sticker', 'Sticker'),
        ('location', 'Location'),
        ('contact', 'Contact'),
        ('callback_query', 'Callback Query'),
        ('inline_query', 'Inline Query'),
        ('command', 'Command'),
    ], string='Message Type', default='text', required=True)
    
    # Direction
    direction = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], string='Direction', required=True, index=True)
    
    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', required=True, tracking=True, index=True)
    
    error_message = fields.Text(
        string='Error Message',
        help='Error description if message failed'
    )
    
    # Relations
    bot_id = fields.Many2one(
        'telegram.bot',
        string='Bot',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    user_id = fields.Many2one(
        'telegram.bot.user',
        string='Telegram User',
        ondelete='set null',
        index=True
    )
    
    chat_id = fields.Char(
        string='Chat ID',
        required=True,
        index=True,
        help='Telegram chat identifier'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='user_id.partner_id',
        store=True
    )
    
    # Parent message for replies
    reply_to_id = fields.Many2one(
        'telegram.message',
        string='Reply To',
        ondelete='set null',
        index=True
    )
    
    # Related Odoo Documents
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        ondelete='set null'
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        ondelete='set null'
    )
    
    # Command Information
    command = fields.Char(
        string='Command',
        help='Bot command if applicable'
    )
    
    command_args = fields.Text(
        string='Command Arguments',
        help='Arguments passed with command'
    )
    
    # Callback Data
    callback_data = fields.Text(
        string='Callback Data',
        help='Data from callback query'
    )
    
    # Response Information
    response_data = fields.Text(
        string='Response Data',
        help='Raw response from Telegram API'
    )
    
    response_time = fields.Float(
        string='Response Time (seconds)',
        help='Time taken to send/receive message'
    )
    
    # Media
    file_id = fields.Char(
        string='File ID',
        help='Telegram file identifier'
    )
    
    file_url = fields.Char(
        string='File URL',
        help='URL to access the file'
    )
    
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    )
    
    # Processing
    is_processed = fields.Boolean(
        string='Processed',
        default=False,
        help='Indicates if message has been processed'
    )
    
    processed_by = fields.Many2one(
        'res.users',
        string='Processed By'
    )
    
    process_date = fields.Datetime(
        string='Process Date'
    )
    
    # Additional Data
    extra_data = fields.Text(
        string='Additional Data',
        help='JSON data with additional message information'
    )
    
    # Metadata
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    create_date = fields.Datetime(string='Created Date', readonly=True, index=True)
    write_date = fields.Datetime(string='Last Updated', readonly=True)

    # ==================== Computed Fields ====================
    
    message_preview = fields.Char(
        string='Preview',
        compute='_compute_message_preview',
        store=False
    )
    
    is_command = fields.Boolean(
        string='Is Command',
        compute='_compute_is_command',
        store=True
    )

    @api.depends('message_text')
    def _compute_message_preview(self):
        """Generate message preview (first 100 chars)"""
        for msg in self:
            if msg.message_text:
                msg.message_preview = msg.message_text[:100] + ('...' if len(msg.message_text) > 100 else '')
            else:
                msg.message_preview = f'[{msg.message_type}]'

    @api.depends('message_text')
    def _compute_is_command(self):
        """Check if message is a bot command"""
        for msg in self:
            msg.is_command = msg.message_text and msg.message_text.startswith('/')

    # ==================== Constraints ====================
    
    @api.constrains('message_text')
    def _check_message_text(self):
        """Validate message text"""
        for msg in self:
            if msg.message_type == 'text' and not msg.message_text:
                raise UserError(_('Message text is required for text messages.'))

    # ==================== Action Methods ====================
    
    def action_resend(self):
        """Resend failed message"""
        for msg in self:
            if msg.state not in ['failed']:
                continue
            
            # Reset status
            msg.state = 'pending'
            msg.error_message = False
            
            # Resend via bot
            if msg.bot_id and msg.chat_id:
                result = msg.bot_id.send_message(msg.chat_id, msg.message_text)
                
                if result.get('ok'):
                    msg.state = 'sent'
                    msg.telegram_message_id = str(result['result']['message_id'])
                    msg.response_data = json.dumps(result)
                else:
                    msg.state = 'failed'
                    msg.error_message = result.get('description', 'Unknown error')
                    msg.response_data = json.dumps(result)

    def action_mark_processed(self):
        """Mark message as processed"""
        for msg in self:
            msg.is_processed = True
            msg.processed_by = self.env.user.id
            msg.process_date = fields.Datetime.now()

    def action_view_chat_history(self):
        """View chat history with this user"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Chat History'),
            'res_model': 'telegram.message',
            'view_mode': 'tree,form',
            'domain': [
                ('chat_id', '=', self.chat_id),
                ('bot_id', '=', self.bot_id.id),
            ],
            'context': {
                'search_default_chat_id': self.chat_id,
                'search_default_bot_id': self.bot_id.id,
            }
        }

    def action_create_task(self):
        """Create task from message"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Task'),
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_name': f'Telegram: {self.message_preview}',
                'default_description': self.message_text,
                'default_partner_id': self.partner_id.id,
            }
        }

    # ==================== Helper Methods ====================
    
    def _log_message(self, bot_id, chat_id, message_data, direction='incoming'):
        """
        Log a message from Telegram update
        
        Args:
            bot_id: Bot record ID
            chat_id: Chat identifier
            message_data: Message data from Telegram
            direction: Message direction
            
        Returns:
            telegram.message: Created message record
        """
        try:
            vals = {
                'bot_id': bot_id,
                'chat_id': str(chat_id),
                'direction': direction,
                'state': 'delivered' if direction == 'incoming' else 'sent',
                'message_type': 'text',
            }
            
            # Extract message content
            if 'text' in message_data:
                vals['message_text'] = message_data['text']
                vals['message_type'] = 'text'
                
                # Check for commands
                if message_data['text'].startswith('/'):
                    parts = message_data['text'].split(' ', 1)
                    vals['command'] = parts[0]
                    vals['command_args'] = parts[1] if len(parts) > 1 else ''
                    vals['message_type'] = 'command'
            
            elif 'photo' in message_data:
                vals['message_type'] = 'photo'
                vals['message_text'] = message_data.get('caption', '')
                # Get largest photo
                photo = message_data['photo'][-1]
                vals['file_id'] = photo['file_id']
            
            elif 'document' in message_data:
                vals['message_type'] = 'document'
                vals['message_text'] = message_data.get('caption', '')
                vals['file_id'] = message_data['document']['file_id']
            
            elif 'voice' in message_data:
                vals['message_type'] = 'voice'
                vals['file_id'] = message_data['voice']['file_id']
            
            elif 'sticker' in message_data:
                vals['message_type'] = 'sticker'
                vals['file_id'] = message_data['sticker']['file_id']
            
            elif 'location' in message_data:
                vals['message_type'] = 'location'
                loc = message_data['location']
                vals['message_text'] = f"Location: {loc['latitude']}, {loc['longitude']}"
            
            elif 'contact' in message_data:
                vals['message_type'] = 'contact'
                contact = message_data['contact']
                vals['message_text'] = f"Contact: {contact.get('first_name', '')} {contact.get('last_name', '')}"
            
            # Set Telegram message ID
            vals['telegram_message_id'] = str(message_data.get('message_id', ''))
            
            # Store extra data
            vals['extra_data'] = json.dumps(message_data)
            
            # Find user
            if 'from' in message_data:
                user_data = message_data['from']
                user = self.env['telegram.bot.user'].search([
                    ('bot_id', '=', bot_id),
                    ('telegram_user_id', '=', str(user_data['id']))
                ], limit=1)
                
                if user:
                    vals['user_id'] = user.id
            
            # Create message
            message = self.create(vals)
            
            # Update user activity
            if message.user_id:
                message.user_id._update_activity()
            
            return message
            
        except Exception as e:
            _logger.error(f"Error logging message: {e}")
            return None

    def _get_message_stats(self, bot_id=None, date_from=None, date_to=None):
        """
        Get message statistics
        
        Args:
            bot_id: Filter by bot
            date_from: Start date
            date_to: End date
            
        Returns:
            dict: Message statistics
        """
        domain = []
        if bot_id:
            domain.append(('bot_id', '=', bot_id))
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        messages = self.search(domain)
        
        return {
            'total': len(messages),
            'incoming': len(messages.filtered(lambda m: m.direction == 'incoming')),
            'outgoing': len(messages.filtered(lambda m: m.direction == 'outgoing')),
            'text': len(messages.filtered(lambda m: m.message_type == 'text')),
            'commands': len(messages.filtered(lambda m: m.is_command)),
            'media': len(messages.filtered(lambda m: m.message_type in ['photo', 'document', 'video', 'audio'])),
            'successful': len(messages.filtered(lambda m: m.state in ['sent', 'delivered', 'read'])),
            'failed': len(messages.filtered(lambda m: m.state == 'failed')),
        }
