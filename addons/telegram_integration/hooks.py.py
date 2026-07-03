# -*- coding: utf-8 -*-
"""
Module hooks for Telegram Integration
"""

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-initialization hook
    Executed before module installation
    
    Args:
        cr: Database cursor
    """
    _logger.info("Telegram Integration pre-init hook executing")
    
    # Check if required modules are installed
    _check_dependencies(cr)
    
    # Prepare database
    _prepare_database(cr)


def post_init_hook(cr, registry):
    """
    Post-initialization hook
    Executed after module installation
    
    Args:
        cr: Database cursor
        registry: Model registry
    """
    _logger.info("Telegram Integration post-init hook executing")
    
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Create default data
        _create_default_data(env)
        
        # Update existing records
        _update_existing_records(env)
        
        # Set system parameters
        _set_system_parameters(env)
        
        # Schedule cron jobs
        _schedule_cron_jobs(env)
    
    _logger.info("Telegram Integration post-init hook completed")


def post_load():
    """
    Post-load hook
    Executed when module is loaded (server startup)
    """
    _logger.info("Telegram Integration module loaded")
    
    # Register signal handlers
    _register_signals()


def uninstall_hook(cr, registry):
    """
    Uninstall hook
    Executed before module uninstallation
    
    Args:
        cr: Database cursor
        registry: Model registry
    """
    _logger.info("Telegram Integration uninstall hook executing")
    
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Remove all webhooks
        bots = env['telegram.bot'].sudo().search([])
        for bot in bots:
            try:
                bot.delete_webhook()
                _logger.info(f"Webhook removed for bot: {bot.name}")
            except Exception as e:
                _logger.error(f"Error removing webhook: {e}")
        
        # Remove scheduled actions
        _remove_cron_jobs(env)
        
        # Clean system parameters
        _clean_system_parameters(env)
    
    _logger.info("Telegram Integration uninstall hook completed")


def _check_dependencies(cr):
    """Check if required modules are installed"""
    required_modules = ['base', 'mail', 'contacts']
    
    cr.execute("""
        SELECT name, state 
        FROM ir_module_module 
        WHERE name IN %s
    """, (tuple(required_modules),))
    
    installed = {row[0]: row[1] for row in cr.fetchall()}
    
    for module in required_modules:
        if installed.get(module) != 'installed':
            _logger.warning(f"Required module not installed: {module}")


def _prepare_database(cr):
    """Prepare database for module installation"""
    # Create necessary indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_telegram_message_chat_id ON telegram_message(chat_id)",
        "CREATE INDEX IF NOT EXISTS idx_telegram_message_bot_id ON telegram_message(bot_id)",
        "CREATE INDEX IF NOT EXISTS idx_telegram_bot_user_telegram_id ON telegram_bot_user(telegram_user_id)",
    ]
    
    for index_sql in indexes:
        try:
            cr.execute(index_sql)
        except Exception as e:
            _logger.warning(f"Error creating index: {e}")


def _create_default_data(env):
    """Create default data after installation"""
    try:
        # Create default command templates
        default_commands = [
            {
                'name': 'start',
                'description': 'Start the bot',
                'action': 'start',
                'sequence': 1,
                'reply_template': """
                Welcome! 👋
                
                I can help you with:
                📦 Order tracking
                💰 Invoice management
                🔍 Product search
                📊 Account summary
                """,
            },
            {
                'name': 'help',
                'description': 'Show help message',
                'action': 'help',
                'sequence': 2,
            },
            {
                'name': 'order_status',
                'description': 'Check order status',
                'action': 'order_status',
                'sequence': 10,
                'accepts_arguments': True,
                'argument_description': 'Order number',
                'argument_example': '/order_status SO001',
            },
            {
                'name': 'invoice_status',
                'description': 'Check invoice status',
                'action': 'invoice_status',
                'sequence': 11,
                'accepts_arguments': True,
                'argument_description': 'Invoice number',
                'argument_example': '/invoice_status INV001',
            },
            {
                'name': 'product_search',
                'description': 'Search products',
                'action': 'product_search',
                'sequence': 12,
                'accepts_arguments': True,
                'argument_description': 'Search term',
                'argument_example': '/product_search laptop',
            },
            {
                'name': 'support',
                'description': 'Contact customer support',
                'action': 'customer_support',
                'sequence': 20,
            },
        ]
        
        # Store as system data
        env['ir.model.data'].sudo().create({
            'name': 'default_commands_template',
            'module': 'telegram_integration',
            'model': 'ir.config_parameter',
            'res_id': env['ir.config_parameter'].sudo().create({
                'key': 'telegram.default_commands',
                'value': str(default_commands),
            }).id,
        })
        
        _logger.info("Default data created successfully")
        
    except Exception as e:
        _logger.error(f"Error creating default data: {e}")


def _update_existing_records(env):
    """Update existing records after installation"""
    try:
        # Add telegram fields to existing partners
        partners = env['res.partner'].sudo().search([
            ('telegram_user_id', '=', False)
        ], limit=0)  # No update needed for all, just ensure field exists
        
        _logger.info(f"Updated existing records")
        
    except Exception as e:
        _logger.error(f"Error updating existing records: {e}")


def _set_system_parameters(env):
    """Set default system parameters"""
    params = env['ir.config_parameter'].sudo()
    
    default_params = {
        'telegram.auto_registration': 'False',
        'telegram.max_message_length': '4096',
        'telegram.max_file_size': '52428800',  # 50 MB
        'telegram.retry_attempts': '3',
        'telegram.retry_delay': '5',
        'telegram.webhook_max_connections': '40',
        'telegram.enable_logging': 'True',
        'telegram.log_level': 'INFO',
    }
    
    for key, value in default_params.items():
        if not params.get_param(key):
            params.set_param(key, value)
            _logger.info(f"Set parameter {key} = {value}")


def _schedule_cron_jobs(env):
    """Schedule cron jobs for periodic tasks"""
    try:
        # Schedule webhook health check
        env['ir.cron'].sudo().create({
            'name': 'Telegram: Webhook Health Check',
            'model_id': env.ref('telegram_integration.model_telegram_bot').id,
            'state': 'code',
            'code': 'model._cron_check_webhooks()',
            'interval_number': 30,
            'interval_type': 'minutes',
            'numbercall': -1,
            'active': True,
        })
        
        # Schedule message cleanup (older than 90 days)
        env['ir.cron'].sudo().create({
            'name': 'Telegram: Clean Old Messages',
            'model_id': env.ref('telegram_integration.model_telegram_message').id,
            'state': 'code',
            'code': 'model._cron_clean_old_messages()',
            'interval_number': 1,
            'interval_type': 'days',
            'numbercall': -1,
            'active': True,
        })
        
        # Schedule statistics update
        env['ir.cron'].sudo().create({
            'name': 'Telegram: Update Statistics',
            'model_id': env.ref('telegram_integration.model_telegram_bot').id,
            'state': 'code',
            'code': 'model._cron_update_statistics()',
            'interval_number': 1,
            'interval_type': 'hours',
            'numbercall': -1,
            'active': True,
        })
        
        _logger.info("Cron jobs scheduled successfully")
        
    except Exception as e:
        _logger.error(f"Error scheduling cron jobs: {e}")


def _remove_cron_jobs(env):
    """Remove scheduled cron jobs"""
    try:
        cron_jobs = env['ir.cron'].sudo().search([
            ('name', 'like', 'Telegram:%')
        ])
        cron_jobs.unlink()
        _logger.info("Cron jobs removed")
        
    except Exception as e:
        _logger.error(f"Error removing cron jobs: {e}")


def _clean_system_parameters(env):
    """Remove system parameters"""
    try:
        params = env['ir.config_parameter'].sudo().search([
            ('key', 'like', 'telegram.%')
        ])
        params.unlink()
        _logger.info("System parameters cleaned")
        
    except Exception as e:
        _logger.error(f"Error cleaning system parameters: {e}")


def _register_signals():
    """Register signal handlers"""
    try:
        # Register post_write signal on sale.order for auto-notification
        from odoo import models
        
        @models.Model.onchange
        def _on_order_confirmed(self):
            """Send notification when order is confirmed"""
            if hasattr(self, 'state') and self.state == 'sale':
                # Send via Telegram
                if hasattr(self, 'partner_id') and self.partner_id.telegram_user_id:
                    self.env['telegram.message'].sudo()._send_order_notification(self)
        
        _logger.info("Signals registered")
        
    except Exception as e:
        _logger.error(f"Error registering signals: {e}")