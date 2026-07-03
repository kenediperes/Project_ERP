# -*- coding: utf-8 -*-
# Part of Odoo Telegram Integration Module
# See LICENSE file for full copyright and licensing details.

"""
Telegram Integration Module for Odoo ERP
========================================

This module provides complete Telegram Bot integration for Odoo ERP system,
enabling automated notifications, customer support, order management,
and real-time communication via Telegram.

Features:
---------
- Multi-bot support with webhook configuration
- Automated notifications for orders, invoices, and shipments
- Bot command system with customizable actions
- Customer authentication via Telegram Login Widget
- Message logging and tracking
- User management and preferences
- REST API for external integrations
- Statistics and reporting dashboard
- Queue-based message processing
- Template-based messaging

Dependencies:
------------
- base
- mail
- contacts
- sale_management (optional)
- account (optional)
- stock (optional)

Author: Your Company
Website: https://yourcompany.com
Version: 17.0.1.0.0
"""

import logging

# Initialize logger
_logger = logging.getLogger(__name__)

# Import all models to register them
from . import models
from . import controllers
from . import wizard

# Define module constants
MODULE_NAME = 'telegram_integration'
MODULE_VERSION = '17.0.1.0.0'

# Constants for Telegram API
TELEGRAM_API_URL = 'https://api.telegram.org'
TELEGRAM_MAX_MESSAGE_LENGTH = 4096
TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# Message states
MESSAGE_STATE = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('sent', 'Sent'),
    ('delivered', 'Delivered'),
    ('read', 'Read'),
    ('failed', 'Failed'),
    ('cancelled', 'Cancelled'),
]

# Bot states
BOT_STATE = [
    ('draft', 'Draft'),
    ('configured', 'Configured'),
    ('running', 'Running'),
    ('error', 'Error'),
    ('stopped', 'Stopped'),
]

# Message types
MESSAGE_TYPE = [
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
]

# Built-in command actions
COMMAND_ACTIONS = [
    ('start', 'Start'),
    ('help', 'Help'),
    ('order_status', 'Check Order Status'),
    ('invoice_status', 'Check Invoice Status'),
    ('product_search', 'Search Products'),
    ('account_summary', 'Account Summary'),
    ('latest_offers', 'Latest Offers'),
    ('customer_support', 'Customer Support'),
    ('contact_info', 'Contact Information'),
    ('business_hours', 'Business Hours'),
    ('track_shipment', 'Track Shipment'),
    ('check_balance', 'Check Balance'),
    ('create_order', 'Create Order'),
    ('custom', 'Custom Action'),
]


def get_telegram_api_url(method, bot_token):
    """
    Generate Telegram API URL for a specific method
    
    Args:
        method: API method name (e.g., 'sendMessage', 'getMe')
        bot_token: Bot token
        
    Returns:
        str: Full API URL
    """
    return f"{TELEGRAM_API_URL}/bot{bot_token}/{method}"


def truncate_message(text, max_length=TELEGRAM_MAX_MESSAGE_LENGTH):
    """
    Truncate message to Telegram's maximum length
    
    Args:
        text: Message text
        max_length: Maximum length (default: 4096)
        
    Returns:
        str: Truncated text
    """
    if len(text) > max_length:
        return text[:max_length - 3] + '...'
    return text


def escape_html(text):
    """
    Escape HTML special characters for Telegram HTML parse mode
    
    Args:
        text: Input text
        
    Returns:
        str: Escaped text
    """
    if not text:
        return text
    
    escape_chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
    }
    
    for char, escaped in escape_chars.items():
        text = text.replace(char, escaped)
    
    return text


def escape_markdown(text):
    """
    Escape Markdown special characters for Telegram Markdown parse mode
    
    Args:
        text: Input text
        
    Returns:
        str: Escaped text
    """
    if not text:
        return text
    
    escape_chars = [
        '_', '*', '[', ']', '(', ')', '~', '`', '>', 
        '#', '+', '-', '=', '|', '{', '}', '.', '!'
    ]
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_currency(amount, currency='IDR'):
    """
    Format currency amount for Telegram messages
    
    Args:
        amount: Numeric amount
        currency: Currency code
        
    Returns:
        str: Formatted currency string
    """
    try:
        # Get currency symbol from Odoo
        currency_obj = None
        try:
            from odoo import api
            if hasattr(api, 'Environment'):
                currency_obj = api.Environment().env['res.currency'].search(
                    [('name', '=', currency)], limit=1
                )
        except:
            pass
        
        if currency_obj:
            return f"{currency_obj.symbol} {amount:,.2f}"
        else:
            return f"{currency} {amount:,.2f}"
    except:
        return f"{amount:,.2f}"


def create_inline_keyboard(buttons, row_width=2):
    """
    Create inline keyboard markup for Telegram
    
    Args:
        buttons: List of button dicts with 'text' and 'callback_data'
        row_width: Number of buttons per row
        
    Returns:
        dict: Inline keyboard markup
    """
    keyboard = []
    current_row = []
    
    for button in buttons:
        current_row.append({
            'text': button.get('text', 'Button'),
            'callback_data': button.get('callback_data', 'default'),
        })
        
        if len(current_row) >= row_width:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row)
    
    return {'inline_keyboard': keyboard}


def create_reply_keyboard(buttons, row_width=2, resize=True, one_time=False):
    """
    Create reply keyboard markup for Telegram
    
    Args:
        buttons: List of button texts
        row_width: Number of buttons per row
        resize: Resize keyboard to fit
        one_time: Hide keyboard after use
        
    Returns:
        dict: Reply keyboard markup
    """
    keyboard = []
    current_row = []
    
    for button_text in buttons:
        current_row.append({'text': button_text})
        
        if len(current_row) >= row_width:
            keyboard.append(current_row)
            current_row = []
    
    if current_row:
        keyboard.append(current_row)
    
    return {
        'keyboard': keyboard,
        'resize_keyboard': resize,
        'one_time_keyboard': one_time,
    }


def remove_keyboard():
    """Create markup to remove keyboard"""
    return {'remove_keyboard': True}


def force_reply(placeholder=None):
    """
    Create force reply markup
    
    Args:
        placeholder: Placeholder text
        
    Returns:
        dict: Force reply markup
    """
    markup = {'force_reply': True}
    if placeholder:
        markup['input_field_placeholder'] = placeholder
    return markup


# Initialize module
def _initialize_module(cr, registry):
    """Initialize module after installation"""
    _logger.info(f"Initializing {MODULE_NAME} v{MODULE_VERSION}")
    
    # Create default system parameters
    env = registry.env if hasattr(registry, 'env') else None
    
    if env:
        # Set default parameters
        params = env['ir.config_parameter'].sudo()
        
        default_params = {
            'telegram.auto_registration': 'False',
            'telegram.max_message_length': str(TELEGRAM_MAX_MESSAGE_LENGTH),
            'telegram.max_file_size': str(TELEGRAM_MAX_FILE_SIZE),
            'telegram.retry_attempts': '3',
            'telegram.retry_delay': '5',
            'telegram.webhook_max_connections': '40',
        }
        
        for key, value in default_params.items():
            if not params.get_param(key):
                params.set_param(key, value)
        
        _logger.info(f"{MODULE_NAME} default parameters set")
    
    _logger.info(f"{MODULE_NAME} initialized successfully")


# Uninstall cleanup
def _uninstall_hook(cr, registry):
    """Cleanup after module uninstallation"""
    _logger.info(f"Cleaning up {MODULE_NAME}")
    
    # Remove webhooks for all bots
    env = registry.env if hasattr(registry, 'env') else None
    
    if env:
        bots = env['telegram.bot'].sudo().search([])
        for bot in bots:
            try:
                bot.delete_webhook()
                _logger.info(f"Webhook removed for bot: {bot.name}")
            except Exception as e:
                _logger.error(f"Error removing webhook for bot {bot.name}: {e}")
    
    _logger.info(f"{MODULE_NAME} cleanup completed")