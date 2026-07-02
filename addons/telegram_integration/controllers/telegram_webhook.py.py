from odoo import http
from odoo.http import request
import json
import logging

_logger = logging.getLogger(__name__)

class TelegramWebhook(http.Controller):
    
    @http.route('/telegram/webhook/<int:bot_id>', type='json', auth='public', csrf=False, methods=['POST'])
    def telegram_webhook(self, bot_id, **kwargs):
        """Handle incoming Telegram webhook"""
        try:
            data = request.jsonrequest
            
            if 'message' in data:
                message = data['message']
                chat_id = message['chat']['id']
                user_id = message['from']['id']
                
                if 'text' in message:
                    text = message['text']
                    
                    # Check if it's a command
                    if text.startswith('/'):
                        return self._handle_command(bot_id, chat_id, user_id, text)
                    else:
                        return self._handle_message(bot_id, chat_id, user_id, text)
            
            return {'status': 'ok'}
            
        except Exception as e:
            _logger.error(f"Telegram webhook error: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _handle_command(self, bot_id, chat_id, user_id, command):
        """Handle bot commands"""
        bot = request.env['telegram.bot'].sudo().browse(bot_id)
        
        # Remove the / from command
        cmd = command.split()[0][1:]
        args = command.split()[1:] if len(command.split()) > 1 else []
        
        # Find matching command
        telegram_cmd = request.env['telegram.command'].sudo().search([
            ('bot_id', '=', bot_id),
            ('name', '=', cmd),
            ('is_active', '=', True)
        ], limit=1)
        
        if telegram_cmd:
            response = self._execute_action(telegram_cmd.action, chat_id, args)
            bot.send_message(chat_id, response)
        else:
            # Default help message
            help_text = self._get_help_text(bot)
            bot.send_message(chat_id, help_text)
        
        return {'status': 'ok'}
    
    def _execute_action(self, action, chat_id, args):
        """Execute bot action"""
        if action == 'order_status':
            return self._check_order_status(chat_id, args)
        elif action == 'invoice_status':
            return self._check_invoice_status(chat_id, args)
        elif action == 'product_search':
            return self._search_products(args)
        elif action == 'account_balance':
            return self._check_balance(chat_id)
        elif action == 'latest_offers':
            return self._get_latest_offers()
        elif action == 'customer_support':
            return "Our support team will contact you shortly. " \
                   "Please email support@yourcompany.com or call +62xxx"
        return "Action not implemented"
    
    def _check_order_status(self, chat_id, order_ref=None):
        """Check order status"""
        if not order_ref:
            return "Please provide order reference. Example: /order_status SO001"
        
        order = request.env['sale.order'].sudo().search([
            ('name', '=', order_ref[0])
        ], limit=1)
        
        if order:
            return f"""
            *Order Status: {order.name}*
            
            Status: {order.state}
            Total: Rp {order.amount_total:,.2f}
            Delivery Status: {order.delivery_status or 'Pending'}
            Expected Date: {order.expected_date or 'TBD'}
            
            Track your order: {order.get_portal_url()}
            """
        return f"Order {order_ref[0]} not found"
    
    def _check_invoice_status(self, chat_id, invoice_ref=None):
        """Check invoice status"""
        if not invoice_ref:
            return "Please provide invoice number. Example: /invoice_status INV001"
        
        invoice = request.env['account.move'].sudo().search([
            ('name', '=', invoice_ref[0]),
            ('move_type', 'in', ['out_invoice', 'out_refund'])
        ], limit=1)
        
        if invoice:
            return f"""
            *Invoice: {invoice.name}*
            
            Amount: Rp {invoice.amount_total:,.2f}
            Due Date: {invoice.invoice_date_due}
            Status: {invoice.payment_state}
            
            Pay now: {invoice.get_portal_url()}
            """
        return f"Invoice {invoice_ref[0]} not found"
    
    def _search_products(self, query):
        """Search products"""
        search_term = ' '.join(query) if query else ''
        if not search_term:
            return "Please provide search term. Example: /product_search laptop"
        
        products = request.env['product.product'].sudo().search([
            ('name', 'ilike', search_term),
            ('sale_ok', '=', True)
        ], limit=5)
        
        if products:
            response = "*Search Results:*\n\n"
            for product in products:
                response += f"📦 {product.name}\n"
                response += f"   Price: Rp {product.list_price:,.2f}\n"
                response += f"   Available: {product.qty_available} units\n\n"
            return response
        return f"No products found for '{search_term}'"
    
    def _get_help_text(self, bot):
        """Get help text with available commands"""
        help_text = "*Available Commands:*\n\n"
        commands = request.env['telegram.command'].sudo().search([
            ('bot_id', '=', bot.id),
            ('is_active', '=', True)
        ])
        
        for cmd in commands:
            help_text += f"/{cmd.name} - {cmd.description}\n"
        
        return help_text