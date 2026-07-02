from odoo import models, fields, api
import json
import requests
import logging

_logger = logging.getLogger(__name__)

class TelegramBot(models.Model):
    _name = 'telegram.bot'
    _description = 'Telegram Bot Configuration'
    
    name = fields.Char(string='Bot Name', required=True)
    bot_token = fields.Char(string='Bot Token', required=True)
    webhook_url = fields.Char(string='Webhook URL', compute='_compute_webhook_url')
    is_active = fields.Boolean(string='Active', default=True)
    
    # Bot commands
    command_ids = fields.One2many('telegram.command', 'bot_id', string='Commands')
    
    # Statistics
    total_users = fields.Integer(string='Total Users')
    total_messages = fields.Integer(string='Total Messages')
    
    @api.depends('bot_token')
    def _compute_webhook_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for bot in self:
            bot.webhook_url = f"{base_url}/telegram/webhook/{bot.id}"
    
    def set_webhook(self):
        """Set Telegram webhook"""
        for bot in self:
            url = f"https://api.telegram.org/bot{bot.bot_token}/setWebhook"
            payload = {'url': bot.webhook_url}
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                bot.message_post(body="Webhook configured successfully")
            else:
                bot.message_post(body=f"Failed to configure webhook: {response.text}")
    
    def send_message(self, chat_id, text, parse_mode='HTML', reply_markup=None):
        """Send message via Telegram"""
        for bot in self:
            url = f"https://api.telegram.org/bot{bot.bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
            }
            
            if reply_markup:
                payload['reply_markup'] = json.dumps(reply_markup)
            
            response = requests.post(url, json=payload)
            return response.json()

class TelegramCommand(models.Model):
    _name = 'telegram.command'
    _description = 'Telegram Bot Commands'
    
    bot_id = fields.Many2one('telegram.bot', string='Bot', required=True)
    name = fields.Char(string='Command', required=True)
    description = fields.Text(string='Description')
    action = fields.Selection([
        ('order_status', 'Check Order Status'),
        ('invoice_status', 'Check Invoice Status'),
        ('product_search', 'Search Products'),
        ('customer_support', 'Customer Support'),
        ('account_balance', 'Check Account Balance'),
        ('latest_offers', 'Latest Offers'),
    ], string='Action', required=True)
    
    reply_template = fields.Text(string='Reply Template')
    is_active = fields.Boolean(string='Active', default=True)