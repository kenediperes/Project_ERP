# -*- coding: utf-8 -*-
"""
Telegram Authentication Controller
Handles Telegram login widget authentication
"""

import json
import logging
import hashlib
import hmac

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class TelegramAuthController(http.Controller):
    """Handle Telegram authentication via Telegram Login Widget"""
    
    @http.route('/telegram/auth/callback', type='http', auth='public', 
                methods=['GET'], csrf=False)
    def telegram_auth_callback(self, **kwargs):
        """
        Handle Telegram login widget callback
        
        Expected parameters:
        - id: Telegram user ID
        - first_name: User's first name
        - last_name: User's last name (optional)
        - username: Telegram username (optional)
        - photo_url: Avatar URL (optional)
        - auth_date: Authentication timestamp
        - hash: Verification hash
        
        Returns:
            Response: Redirect to appropriate page
        """
        try:
            # Get parameters from callback
            telegram_id = kwargs.get('id')
            first_name = kwargs.get('first_name', '')
            last_name = kwargs.get('last_name', '')
            username = kwargs.get('username', '')
            photo_url = kwargs.get('photo_url', '')
            auth_date = kwargs.get('auth_date')
            received_hash = kwargs.get('hash')
            
            # Verify the data
            if not self._verify_telegram_auth(kwargs):
                _logger.warning("Telegram auth: Invalid hash")
                return request.redirect('/web/login?error=invalid_telegram_auth')
            
            # Find or create user
            partner = self._find_or_create_partner(
                telegram_id, first_name, last_name, username, photo_url
            )
            
            # Log the user in
            if partner and partner.user_ids:
                user = partner.user_ids[0]
                # Create session
                request.session.authenticate(request.db, user.login, user.id)
                return request.redirect('/web')
            else:
                # Create new user if configured
                if self._is_auto_registration_enabled():
                    user = self._create_user_from_telegram(
                        telegram_id, first_name, last_name, username
                    )
                    request.session.authenticate(request.db, user.login, user.id)
                    return request.redirect('/web')
                else:
                    return request.redirect('/web/login?error=no_odoo_user')
                    
        except Exception as e:
            _logger.error(f"Telegram auth error: {str(e)}", exc_info=True)
            return request.redirect('/web/login?error=telegram_auth_error')
    
    def _verify_telegram_auth(self, data):
        """
        Verify Telegram authentication data
        
        Args:
            data: Authentication data from Telegram
            
        Returns:
            bool: True if valid
        """
        try:
            # Get bot token
            bot = request.env['telegram.bot'].sudo().search(
                [('is_active', '=', True)], limit=1
            )
            
            if not bot:
                _logger.warning("No active bot found for auth verification")
                return False
            
            # Create data check string
            check_hash = data.get('hash', '')
            data_check_string = self._create_data_check_string(data)
            
            # Calculate secret key
            secret_key = hashlib.sha256(bot.bot_token.encode('utf-8')).digest()
            
            # Calculate hash
            calculated_hash = hmac.new(
                secret_key,
                data_check_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return calculated_hash == check_hash
            
        except Exception as e:
            _logger.error(f"Auth verification error: {str(e)}")
            return False
    
    def _create_data_check_string(self, data):
        """
        Create data check string for verification
        
        Args:
            data: Authentication data
            
        Returns:
            str: Data check string
        """
        # Remove hash from data
        check_data = {k: v for k, v in data.items() if k != 'hash'}
        
        # Sort alphabetically and create string
        sorted_items = sorted(check_data.items())
        data_check_arr = [f"{k}={v}" for k, v in sorted_items]
        
        return '\n'.join(data_check_arr)
    
    def _find_or_create_partner(self, telegram_id, first_name, last_name, username, photo_url):
        """
        Find existing partner or create new one
        
        Args:
            telegram_id: Telegram user ID
            first_name: First name
            last_name: Last name
            username: Username
            photo_url: Photo URL
            
        Returns:
            res.partner: Partner record
        """
        Partner = request.env['res.partner'].sudo()
        
        # Search by Telegram ID
        partner = Partner.search([
            ('telegram_user_id', '=', telegram_id)
        ], limit=1)
        
        if partner:
            # Update information
            partner.write({
                'telegram_username': username,
                'first_name': first_name,
                'last_name': last_name,
            })
            return partner
        
        # Search by name and email-like username
        email = f"{username}@telegram.com" if username else f"user{telegram_id}@telegram.com"
        
        partner = Partner.search([
            ('email', '=', email)
        ], limit=1)
        
        if partner:
            partner.write({
                'telegram_user_id': telegram_id,
                'telegram_username': username,
            })
            return partner
        
        return None
    
    def _is_auto_registration_enabled(self):
        """Check if auto-registration is enabled"""
        return request.env['ir.config_parameter'].sudo().get_param(
            'telegram.auto_registration', 'False'
        ) == 'True'
    
    def _create_user_from_telegram(self, telegram_id, first_name, last_name, username):
        """
        Create Odoo user from Telegram data
        
        Args:
            telegram_id: Telegram user ID
            first_name: First name
            last_name: Last name
            username: Username
            
        Returns:
            res.users: User record
        """
        # Create partner
        partner = request.env['res.partner'].sudo().create({
            'name': f"{first_name} {last_name}".strip(),
            'first_name': first_name,
            'last_name': last_name,
            'telegram_user_id': telegram_id,
            'telegram_username': username,
            'email': f"{username}@telegram.com" if username else f"user{telegram_id}@telegram.com",
            'customer_rank': 1,
        })
        
        # Create portal user
        user = request.env['res.users'].sudo().create({
            'name': partner.name,
            'login': partner.email,
            'partner_id': partner.id,
            'groups_id': [(6, 0, [
                request.env.ref('base.group_portal').id
            ])],
        })
        
        return user
    
    @http.route('/telegram/auth/login', type='http', auth='public', methods=['GET'])
    def telegram_login_page(self, **kwargs):
        """
        Display Telegram login page
        
        Returns:
            str: HTML page with Telegram login widget
        """
        bot = request.env['telegram.bot'].sudo().search(
            [('is_active', '=', True)], limit=1
        )
        
        if not bot:
            return Response(
                '<h1>Telegram login is not configured</h1>',
                status=404,
                content_type='text/html'
            )
        
        bot_name = bot.name
        callback_url = request.httprequest.url_root + 'telegram/auth/callback'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login with Telegram</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }}
                .login-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                    text-align: center;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="login-container">
                <h1>Login with Telegram</h1>
                <script async 
                        src="https://telegram.org/js/telegram-widget.js?22" 
                        data-telegram-login="{bot_name}" 
                        data-size="large" 
                        data-auth-url="{callback_url}" 
                        data-request-access="write">
                </script>
            </div>
        </body>
        </html>
        """
        
        return Response(html, content_type='text/html')