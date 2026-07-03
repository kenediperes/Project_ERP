# -*- coding: utf-8 -*-
# Part of Odoo Telegram Integration Module
# See LICENSE file for full copyright and licensing details.

{
    # ==================== BASIC INFORMATION ====================
    
    'name': 'Telegram Integration for Odoo ERP',
    'version': '17.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrate Telegram Bot with Odoo ERP System',
    'description': """
        Telegram Integration for Odoo ERP
        ==================================
        
        This module provides complete Telegram Bot integration for your Odoo ERP system,
        enabling automated notifications, customer support, order management,
        and real-time communication via Telegram.
        
        Key Features:
        -------------
        * Multi-Bot Support
          - Configure multiple Telegram bots for different purposes
          - Webhook-based real-time updates
          - Secure token verification
        
        * Automated Notifications
          - Order confirmations and status updates
          - Invoice notifications and payment reminders
          - Shipping and delivery updates
          - Custom notification templates
        
        * Customer Support
          - Automated responses to common queries
          - Order and invoice status checking
          - Product search and information
          - Live chat with support team
        
        * Bot Commands System
          - Pre-built commands (/start, /help, /order_status, etc.)
          - Custom command creation
          - Command permissions and access control
          - Usage statistics and analytics
        
        * Customer Management
          - Link Telegram users to Odoo partners
          - Telegram Login Widget integration
          - User preferences and opt-out management
          - Chat history and interaction tracking
        
        * Message Management
          - Complete message logging
          - Message templates with dynamic content
          - Bulk messaging and broadcasts
          - Media file handling (photos, documents, etc.)
        
        * Integration Features
          - Sales order integration
          - Invoice and accounting integration
          - Inventory and stock management
          - CRM and lead management
          - HR and employee notifications
        
        * Security & Compliance
          - HTTPS webhook endpoints
          - Secret token verification
          - User authentication
          - Permission-based access control
          - Data privacy controls
        
        * Analytics & Reporting
          - Bot usage statistics
          - User engagement metrics
          - Message delivery reports
          - Command usage analytics
          - Response time tracking
        
        Technical Specifications:
        ------------------------
        - Supports Telegram Bot API v6.0+
        - Webhook and long-polling support
        - Async message processing
        - Redis queue integration (optional)
        - REST API for external integrations
        - Compatible with Odoo 17.0 Community and Enterprise
        
        Use Cases:
        ---------
        1. E-commerce: Order notifications, shipping updates, invoice delivery
        2. Customer Service: Automated FAQ, ticket creation, live support
        3. Sales: Lead notifications, quotation delivery, follow-up reminders
        4. HR: Leave approvals, attendance notifications, company announcements
        5. Operations: Inventory alerts, delivery confirmations, task assignments
        
        Installation:
        ------------
        1. Install this module from Apps menu
        2. Go to Telegram > Bots and create a new bot configuration
        3. Get bot token from @BotFather on Telegram
        4. Configure webhook URL automatically
        5. Set up commands and templates as needed
        6. Start engaging with customers via Telegram!
        
        Configuration:
        -------------
        1. Create a bot via @BotFather on Telegram
        2. Copy the bot token
        3. In Odoo, go to Telegram > Configuration > Bots
        4. Create new bot with the token
        5. Click "Set Webhook" to configure automatic updates
        6. Configure commands and message templates
        7. Enable automatic notifications in Settings
        
        Support:
        -------
        For support, bug reports, or feature requests:
        - Email: support@yourcompany.com
        - Telegram: @yourcompany_support
        - Website: https://yourcompany.com/odoo-telegram
        
        Developed by: Your Company
        Website: https://yourcompany.com
        Version: 17.0.1.0.0
        License: LGPL-3
    """,
    
    # ==================== AUTHOR & WEBSITE ====================
    
    'author': 'Your Company Name',
    'website': 'https://yourcompany.com',
    'support': 'support@yourcompany.com',
    'maintainer': 'Your Company Name',
    
    # ==================== LICENSE ====================
    
    'license': 'LGPL-3',
    
    # ==================== DEPENDENCIES ====================
    
    'depends': [
        # Core Odoo Modules
        'base',                         # Base module
        'mail',                         # Messaging and email
        'contacts',                     # Contact management
        'web',                          # Web framework
        
        # Optional but recommended
        'sale_management',              # Sales management
        'account',                      # Accounting and invoicing
        'stock',                        # Inventory management
        'crm',                          # CRM
        'hr',                           # Human resources
        'project',                      # Project management
        
        # Technical dependencies
        'base_setup',                   # Base setup
        'web_tour',                     # Web tours (for onboarding)
    ],
    
    # ==================== DATA FILES ====================
    
    'data': [
        # Security
        'security/telegram_security.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        
        # Data
        'data/telegram_command_data.xml',
        'data/telegram_template_data.xml',
        'data/mail_template_data.xml',
        'data/cron_jobs.xml',
        'data/ir_config_parameter.xml',
        
        # Views
        'views/telegram_views.xml',
        'views/telegram_bot_views.xml',
        'views/telegram_user_views.xml',
        'views/telegram_message_views.xml',
        'views/telegram_command_views.xml',
        'views/telegram_template_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/telegram_dashboard_views.xml',
        
        # Wizards
        'wizards/send_message_wizard.xml',
        'wizards/broadcast_wizard.xml',
        'wizards/import_users_wizard.xml',
        
        # Reports
        'reports/telegram_report_views.xml',
        'reports/telegram_message_report.xml',
        
        # Menu
        'views/telegram_menu.xml',
    ],
    
    # ==================== DEMO DATA ====================
    
    'demo': [
        'demo/telegram_bot_demo.xml',
        'demo/telegram_user_demo.xml',
        'demo/telegram_command_demo.xml',
        'demo/telegram_template_demo.xml',
    ],
    
    # ==================== ASSETS ====================
    
    'assets': {
        'web.assets_backend': [
            'telegram_integration/static/src/js/telegram_widget.js',
            'telegram_integration/static/src/js/telegram_dashboard.js',
            'telegram_integration/static/src/js/telegram_message_preview.js',
            'telegram_integration/static/src/scss/telegram_style.scss',
            'telegram_integration/static/src/xml/telegram_templates.xml',
        ],
        'web.assets_frontend': [
            'telegram_integration/static/src/js/telegram_login_widget.js',
            'telegram_integration/static/src/js/telegram_chat_widget.js',
            'telegram_integration/static/src/scss/telegram_frontend.scss',
        ],
        'web.qunit_suite_tests': [
            'telegram_integration/static/tests/**/*.js',
        ],
    },
    
    # ==================== EXTERNAL DEPENDENCIES ====================
    
    'external_dependencies': {
        'python': [
            'requests',          # HTTP requests to Telegram API
            'python-telegram-bot>=20.0',  # Telegram Bot API wrapper (optional)
        ],
        'bin': [],               # Binary dependencies
    },
    
    # ==================== APPLICATION CONFIGURATION ====================
    
    'application': True,        # This is a full application
    'installable': True,        # Module can be installed
    'auto_install': False,      # Don't auto-install
    'sequence': 50,             # Position in app list
    
    # ==================== PRICE & CURRENCY ====================
    
    'price': 0.00,              # Free (change for commercial version)
    'currency': 'EUR',
    
    # ==================== IMAGES & ICONS ====================
    
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/screenshot_1.png',
        'static/description/screenshot_2.png',
        'static/description/screenshot_3.png',
        'static/description/screenshot_4.png',
        'static/description/screenshot_5.png',
    ],
    
    # ==================== CUSTOM HOOKS ====================
    
    'pre_init_hook': 'hooks.pre_init_hook',
    'post_init_hook': 'hooks.post_init_hook',
    'post_load': 'hooks.post_load',
    'uninstall_hook': 'hooks.uninstall_hook',
    
    # ==================== UNINSTALL ====================
    
    'uninstall_hook': 'hooks.uninstall_hook',
}

# ==================== MODULE METADATA ====================
# Additional metadata for Odoo App Store

MODULE_METADATA = {
    'technical_name': 'telegram_integration',
    'category': 'Discuss',
    'complexity': 'advanced',
    'certificate': False,
    'featured': True,
    'subscription': False,
}
