{
    'name': 'WhatsApp Integration',
    'version': '17.0.1.0.0',
    'category': 'Discuss',
    'summary': 'Integrate WhatsApp with Odoo ERP',
    'description': """
        WhatsApp Integration for Odoo ERP
        - Send/Receive WhatsApp messages
        - Template messages
        - Customer notifications
        - Order updates via WhatsApp
        - Invoice sharing
    """,
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'depends': [
        'base',
        'mail',
        'contacts',
        'sale_management',
        'account',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'data/whatsapp_template_data.xml',
        'wizards/send_whatsapp_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}