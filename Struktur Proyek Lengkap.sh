odoo-erp-messaging/
├── docker-compose.yml
├── .env
├── config/
│   └── odoo.conf
├── addons/
│   ├── whatsapp_integration/
│   │   ├── __init__.py
│   │   ├── __manifest__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── whatsapp_message.py
│   │   │   └── res_partner.py
│   │   ├── controllers/
│   │   │   ├── __init__.py
│   │   │   └── whatsapp_webhook.py
│   │   ├── views/
│   │   │   └── whatsapp_views.xml
│   │   └── security/
│   │       └── ir.model.access.csv
│   └── telegram_integration/
│       ├── __init__.py
│       ├── __manifest__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── telegram_bot.py
│       │   └── telegram_message.py
│       ├── controllers/
│       │   ├── __init__.py
│       │   └── telegram_webhook.py
│       └── views/
│           └── telegram_views.xml
├── nginx/
│   └── nginx.conf
└── scripts/
    └── init.sh