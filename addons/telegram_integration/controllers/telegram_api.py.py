# -*- coding: utf-8 -*-
"""
Telegram API Controller
Provides REST API endpoints for managing Telegram integration
"""

import json
import logging
from datetime import datetime

from odoo import http, fields
from odoo.http import request, Response
from werkzeug.exceptions import BadRequest, NotFound, Forbidden

_logger = logging.getLogger(__name__)


class TelegramAPIController(http.Controller):
    """REST API for Telegram integration management"""
    
    # ==================== Bot Management ====================
    
    @http.route('/api/telegram/bots', type='json', auth='user', methods=['GET'])
    def get_bots(self, **kwargs):
        """
        Get list of configured Telegram bots
        
        Returns:
            list: List of bot configurations
        """
        bots = request.env['telegram.bot'].search([])
        
        return [{
            'id': bot.id,
            'name': bot.name,
            'is_active': bot.is_active,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages,
            'webhook_url': bot.webhook_url,
        } for bot in bots]
    
    @http.route('/api/telegram/bots/<int:bot_id>', type='json', auth='user', methods=['GET'])
    def get_bot(self, bot_id, **kwargs):
        """
        Get specific bot configuration
        
        Args:
            bot_id: Bot ID
            
        Returns:
            dict: Bot configuration
        """
        bot = request.env['telegram.bot'].browse(bot_id)
        
        if not bot.exists():
            return {'error': 'Bot not found'}
        
        return {
            'id': bot.id,
            'name': bot.name,
            'bot_token': '***hidden***',
            'is_active': bot.is_active,
            'webhook_url': bot.webhook_url,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages,
            'commands': [{
                'id': cmd.id,
                'name': cmd.name,
                'description': cmd.description,
                'action': cmd.action,
                'is_active': cmd.is_active,
            } for cmd in bot.command_ids],
        }
    
    @http.route('/api/telegram/bots', type='json', auth='user', methods=['POST'])
    def create_bot(self, **kwargs):
        """
        Create new bot configuration
        
        Returns:
            dict: Created bot data
        """
        try:
            data = request.jsonrequest
            
            bot = request.env['telegram.bot'].create({
                'name': data.get('name'),
                'bot_token': data.get('bot_token'),
                'is_active': data.get('is_active', True),
            })
            
            # Set webhook automatically
            bot.set_webhook()
            
            return {
                'success': True,
                'bot_id': bot.id,
                'webhook_url': bot.webhook_url,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/telegram/bots/<int:bot_id>', type='json', auth='user', methods=['PUT'])
    def update_bot(self, bot_id, **kwargs):
        """
        Update bot configuration
        
        Args:
            bot_id: Bot ID
            
        Returns:
            dict: Update status
        """
        try:
            bot = request.env['telegram.bot'].browse(bot_id)
            
            if not bot.exists():
                return {'error': 'Bot not found'}
            
            data = request.jsonrequest
            bot.write(data)
            
            return {'success': True}
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # ==================== Message Management ====================
    
    @http.route('/api/telegram/send', type='json', auth='user', methods=['POST'])
    def send_message(self, **kwargs):
        """
        Send message via Telegram bot
        
        Returns:
            dict: Send status
        """
        try:
            data = request.jsonrequest
            
            required_fields = ['bot_id', 'chat_id', 'message']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}
            
            bot = request.env['telegram.bot'].browse(data['bot_id'])
            
            if not bot.exists():
                return {'error': 'Bot not found'}
            
            # Create message record
            message = request.env['telegram.message'].create({
                'bot_id': bot.id,
                'chat_id': data['chat_id'],
                'message_text': data['message'],
                'direction': 'outgoing',
                'state': 'pending',
                'message_type': data.get('message_type', 'text'),
            })
            
            # Send via bot
            response = bot.send_message(
                chat_id=data['chat_id'],
                text=data['message'],
                parse_mode=data.get('parse_mode', 'HTML'),
                reply_markup=data.get('reply_markup')
            )
            
            # Update message status
            if response.get('ok'):
                message.write({
                    'state': 'sent',
                    'response_data': json.dumps(response)
                })
                return {
                    'success': True,
                    'message_id': message.id,
                    'telegram_message_id': response['result']['message_id']
                }
            else:
                message.write({
                    'state': 'failed',
                    'error_message': response.get('description', 'Unknown error')
                })
                return {
                    'success': False,
                    'error': response.get('description')
                }
                
        except Exception as e:
            _logger.error(f"Send message error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/api/telegram/messages', type='json', auth='user', methods=['GET'])
    def get_messages(self, **kwargs):
        """
        Get message history with filters
        
        Returns:
            list: List of messages
        """
        domain = []
        
        # Apply filters
        if 'bot_id' in kwargs:
            domain.append(('bot_id', '=', int(kwargs['bot_id'])))
        if 'chat_id' in kwargs:
            domain.append(('chat_id', '=', kwargs['chat_id']))
        if 'direction' in kwargs:
            domain.append(('direction', '=', kwargs['direction']))
        if 'state' in kwargs:
            domain.append(('state', '=', kwargs['state']))
        
        # Date range
        if 'date_from' in kwargs:
            domain.append(('create_date', '>=', kwargs['date_from']))
        if 'date_to' in kwargs:
            domain.append(('create_date', '<=', kwargs['date_to']))
        
        limit = min(int(kwargs.get('limit', 50)), 200)
        offset = int(kwargs.get('offset', 0))
        
        messages = request.env['telegram.message'].search(
            domain, limit=limit, offset=offset, order='create_date desc'
        )
        
        return [{
            'id': msg.id,
            'bot_id': msg.bot_id.id,
            'chat_id': msg.chat_id,
            'message_text': msg.message_text,
            'direction': msg.direction,
            'state': msg.state,
            'message_type': msg.message_type,
            'create_date': msg.create_date.strftime('%Y-%m-%d %H:%M:%S'),
        } for msg in messages]
    
    # ==================== Statistics ====================
    
    @http.route('/api/telegram/stats/<int:bot_id>', type='json', auth='user', methods=['GET'])
    def get_bot_stats(self, bot_id, **kwargs):
        """
        Get bot statistics
        
        Args:
            bot_id: Bot ID
            
        Returns:
            dict: Bot statistics
        """
        bot = request.env['telegram.bot'].browse(bot_id)
        
        if not bot.exists():
            return {'error': 'Bot not found'}
        
        # Calculate statistics
        today = fields.Date.today()
        
        messages_today = request.env['telegram.message'].search_count([
            ('bot_id', '=', bot_id),
            ('create_date', '>=', today),
        ])
        
        users_today = request.env['telegram.bot.user'].search_count([
            ('bot_id', '=', bot_id),
            ('last_interaction', '>=', today),
        ])
        
        incoming_messages = request.env['telegram.message'].search_count([
            ('bot_id', '=', bot_id),
            ('direction', '=', 'incoming'),
        ])
        
        outgoing_messages = request.env['telegram.message'].search_count([
            ('bot_id', '=', bot_id),
            ('direction', '=', 'outgoing'),
        ])
        
        return {
            'total_users': bot.total_users,
            'total_messages': bot.total_messages,
            'messages_today': messages_today,
            'users_active_today': users_today,
            'incoming_messages': incoming_messages,
            'outgoing_messages': outgoing_messages,
            'success_rate': calculate_success_rate(bot),
        }


def calculate_success_rate(bot):
    """Calculate message success rate"""
    total = request.env['telegram.message'].sudo().search_count([
        ('bot_id', '=', bot.id),
        ('direction', '=', 'outgoing'),
    ])
    
    if total == 0:
        return 100.0
    
    successful = request.env['telegram.message'].sudo().search_count([
        ('bot_id', '=', bot.id),
        ('direction', '=', 'outgoing'),
        ('state', 'in', ['sent', 'delivered']),
    ])
    
    return round((successful / total) * 100, 2)