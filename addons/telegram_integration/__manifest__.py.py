{
    'name': 'Telegram Integration',
    'version': '17.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrate Telegram with Odoo ERP',
    'description': """
        Telegram Bot Integration for Odoo ERP
        - Automated notifications
        - Command-based interactions
        - Order tracking
        - Invoice management
        - Customer support
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'mail',
        'contacts',
        'sale_management',
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/telegram_views.xml',
        'views/res_partner_views.xml',
        'data/telegram_command_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}