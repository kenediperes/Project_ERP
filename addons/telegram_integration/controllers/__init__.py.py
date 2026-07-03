# -*- coding: utf-8 -*-
# Part of Odoo Telegram Integration Module
# See LICENSE file for full copyright and licensing details.

"""
Telegram Integration Controllers

This package contains all HTTP controllers for the Telegram integration:
- Webhook handler for receiving Telegram updates
- API endpoints for bot management
- Message handling endpoints
"""

from . import telegram_webhook
from . import telegram_api
from . import telegram_auth