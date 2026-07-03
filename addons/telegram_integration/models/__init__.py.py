# -*- coding: utf-8 -*-
# Part of Odoo Telegram Integration Module
# See LICENSE file for full copyright and licensing details.

"""
Telegram Integration Models

This package contains all data models for the Telegram integration:
- Bot configuration and management
- Bot users and chat tracking
- Message logging and history
- Command handling and processing
- Template management
- Update processing
"""

from . import telegram_bot
from . import telegram_user
from . import telegram_message
from . import telegram_command
from . import telegram_template
from . import telegram_update
from . import telegram_queue
from . import res_partner
from . import res_config_settings