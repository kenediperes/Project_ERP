# -*- coding: utf-8 -*-
"""
Telegram Webhook Controller
Handles incoming webhook requests from Telegram API
"""

import json
import logging
import hashlib
import hmac

from odoo import http
from odoo.http import request, Response
from werkzeug.exceptions import Forbidden, BadRequest, NotFound

_logger = logging.getLogger(__name__)


class TelegramWebhookController(http.Controller):
    """Handle incoming webhook requests from Telegram"""
    
    @http.route('/telegram/webhook/<int:bot_id>', type='json', auth='public', 
                methods=['POST'], csrf=False, cors='*')
    def telegram_webhook(self, bot_id, **kwargs):
        """
        Main webhook endpoint for receiving Telegram updates
        
        Args:
            bot_id: ID of the Telegram bot configuration
            
        Returns:
            dict: Response status
        """
        try:
            # Get the bot configuration
            bot = request.env['telegram.bot'].sudo().browse(bot_id)
            
            if not bot.exists():
                _logger.error(f"Telegram webhook: Bot {bot_id} not found")
                return {'status': 'error', 'message': 'Bot not found'}
            
            if not bot.is_active:
                _logger.warning(f"Telegram webhook: Bot {bot_id} is inactive")
                return {'status': 'error', 'message': 'Bot is inactive'}
            
            # Get the JSON data from the request
            data = request.jsonrequest
            
            if not data:
                _logger.warning("Telegram webhook: No data received")
                return {'status': 'error', 'message': 'No data received'}
            
            _logger.info(f"Telegram webhook received update: {data.get('update_id')}")
            
            # Process the update asynchronously to avoid timeout
            self._process_update_async(bot, data)
            
            # Always return 200 OK to Telegram
            return {'status': 'ok', 'message': 'Update received'}
            
        except Exception as e:
            _logger.error(f"Telegram webhook error: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
    
    @http.route('/telegram/webhook/<int:bot_id>/test', type='http', auth='user', 
                methods=['GET'], csrf=False)
    def telegram_webhook_test(self, bot_id, **kwargs):
        """
        Test endpoint to verify webhook configuration
        
        Args:
            bot_id: ID of the Telegram bot
            
        Returns:
            str: HTML response with test results
        """
        bot = request.env['telegram.bot'].sudo().browse(bot_id)
        
        if not bot.exists():
            return Response(
                '<h1>Error: Bot not found</h1>',
                status=404,
                content_type='text/html'
            )
        
        # Test webhook URL
        test_data = {
            'bot_name': bot.name,
            'webhook_url': bot.webhook_url,
            'is_active': bot.is_active,
            'total_users': bot.total_users,
            'total_messages': bot.total_messages,
        }
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Webhook Test</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .info {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                pre {{ background: #f8f8f8; padding: 15px; border-radius: 3px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Telegram Webhook Test</h1>
                <div class="info">
                    <h2>Bot Configuration</h2>
                    <pre>{json.dumps(test_data, indent=2)}</pre>
                </div>
                <p class="success">✅ Webhook URL is configured</p>
                <p>Send a message to your bot on Telegram to test the connection.</p>
            </div>
        </body>
        </html>
        """
        
        return Response(html_response, content_type='text/html')
    
    def _process_update_async(self, bot, data):
        """
        Process Telegram update asynchronously
        
        Args:
            bot: Telegram bot record
            data: Update data from Telegram
        """
        try:
            # Use queue job for async processing if available
            if hasattr(request.env, 'queue'):
                request.env['telegram.update'].with_delay().process_update(bot.id, data)
            else:
                # Process directly if queue is not available
                request.env['telegram.update'].sudo().process_update(bot.id, data)
                
        except Exception as e:
            _logger.error(f"Failed to process update async: {str(e)}")
            # Fallback to direct processing
            request.env['telegram.update'].sudo().process_update(bot.id, data)
    
    @http.route('/telegram/setup/<int:bot_id>', type='http', auth='user', 
                methods=['GET'], csrf=False)
    def telegram_setup_page(self, bot_id, **kwargs):
        """
        Setup page for configuring the bot with Telegram
        
        Args:
            bot_id: ID of the Telegram bot
            
        Returns:
            str: HTML setup page
        """
        bot = request.env['telegram.bot'].sudo().browse(bot_id)
        
        if not bot.exists():
            return Response('<h1>Bot not found</h1>', status=404, content_type='text/html')
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Telegram Bot Setup</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #0088cc; }}
                .step {{
                    margin: 20px 0;
                    padding: 20px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border-left: 4px solid #0088cc;
                }}
                .step h3 {{ margin-top: 0; }}
                code {{
                    background: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 14px;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #0088cc;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .button:hover {{ background: #006699; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .info-box {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Telegram Bot Setup</h1>
                
                <div class="info-box">
                    <h2>{bot.name}</h2>
                    <p>Status: <span class="{'success' if bot.is_active else 'warning'}">
                        {'✅ Active' if bot.is_active else '⚠️ Inactive'}
                    </span></p>
                </div>
                
                <div class="step">
                    <h3>Step 1: Create Bot on Telegram</h3>
                    <p>Open Telegram and search for <code>@BotFather</code></p>
                    <p>Send the command <code>/newbot</code> and follow the instructions</p>
                    <p>Copy the bot token provided by BotFather</p>
                </div>
                
                <div class="step">
                    <h3>Step 2: Configure Bot Token</h3>
                    <p>Enter the token in the bot configuration form in Odoo</p>
                    <p>Current webhook URL: <code>{bot.webhook_url}</code></p>
                </div>
                
                <div class="step">
                    <h3>Step 3: Set Webhook</h3>
                    <p>Click the button below to set the webhook automatically:</p>
                    <a href="/web#id={bot.id}&model=telegram.bot&view_type=form" 
                       class="button" target="_blank">
                        Open Bot Configuration
                    </a>
                    <p>Or manually set webhook by visiting:</p>
                    <code>https://api.telegram.org/bot[YOUR_TOKEN]/setWebhook?url={bot.webhook_url}</code>
                </div>
                
                <div class="step">
                    <h3>Step 4: Test the Bot</h3>
                    <p>Send a message to your bot on Telegram</p>
                    <p>Try commands like <code>/start</code> or <code>/help</code></p>
                </div>
                
                <div class="step">
                    <h3>Available Commands</h3>
                    <ul>
                        <li><code>/start</code> - Start the bot</li>
                        <li><code>/help</code> - Show help message</li>
                        <li><code>/order_status [number]</code> - Check order status</li>
                        <li><code>/invoice_status [number]</code> - Check invoice status</li>
                        <li><code>/product_search [keyword]</code> - Search products</li>
                        <li><code>/account_summary</code> - View account summary</li>
                        <li><code>/support</code> - Contact support</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        
        return Response(html_response, content_type='text/html')


class TelegramHealthCheck(http.Controller):
    """Health check endpoints for monitoring"""
    
    @http.route('/telegram/health', type='http', auth='public', methods=['GET'], csrf=False)
    def health_check(self, **kwargs):
        """
        Health check endpoint for load balancers and monitoring
        
        Returns:
            Response: JSON health status
        """
        try:
            # Check if any bots are active
            active_bots = request.env['telegram.bot'].sudo().search_count([
                ('is_active', '=', True)
            ])
            
            health_data = {
                'status': 'healthy' if active_bots > 0 else 'degraded',
                'service': 'telegram_integration',
                'active_bots': active_bots,
                'timestamp': fields.Datetime.now(),
            }
            
            return Response(
                json.dumps(health_data),
                status=200,
                content_type='application/json'
            )
            
        except Exception as e:
            _logger.error(f"Health check failed: {str(e)}")
            return Response(
                json.dumps({
                    'status': 'unhealthy',
                    'error': str(e)
                }),
                status=500,
                content_type='application/json'
            )
    
    @http.route('/telegram/ping', type='http', auth='public', methods=['GET'], csrf=False)
    def ping(self, **kwargs):
        """
        Simple ping endpoint
        
        Returns:
            str: Pong response
        """
        return "pong"