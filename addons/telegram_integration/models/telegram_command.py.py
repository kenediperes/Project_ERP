# -*- coding: utf-8 -*-
"""
Telegram Command Model
Configure bot commands and their handlers
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TelegramCommand(models.Model):
    _name = 'telegram.command'
    _description = 'Telegram Bot Command'
    _order = 'sequence, name'
    _rec_name = 'name'

    # Command Definition
    name = fields.Char(
        string='Command',
        required=True,
        help='Command name without slash (e.g., start, help)'
    )
    
    description = fields.Text(
        string='Description',
        required=True,
        help='Command description shown in /help'
    )
    
    full_command = fields.Char(
        string='Full Command',
        compute='_compute_full_command',
        store=True
    )
    
    # Action Configuration
    action = fields.Selection([
        ('start', 'Start'),
        ('help', 'Help'),
        ('order_status', 'Check Order Status'),
        ('invoice_status', 'Check Invoice Status'),
        ('product_search', 'Search Products'),
        ('account_summary', 'Account Summary'),
        ('latest_offers', 'Latest Offers'),
        ('customer_support', 'Customer Support'),
        ('contact_info', 'Contact Information'),
        ('business_hours', 'Business Hours'),
        ('track_shipment', 'Track Shipment'),
        ('check_balance', 'Check Balance'),
        ('create_order', 'Create Order'),
        ('custom', 'Custom Action'),
    ], string='Action', required=True)
    
    custom_action = fields.Char(
        string='Custom Action Code',
        help='Python code to execute for custom action'
    )
    
    custom_handler = fields.Char(
        string='Handler Method',
        help='Model method to call for custom action (e.g., sale.order.action_confirm)'
    )
    
    # Response Configuration
    reply_template = fields.Html(
        string='Reply Template',
        sanitize=False,
        help='Template for bot response. Use {placeholders} for dynamic content.'
    )
    
    reply_type = fields.Selection([
        ('text', 'Text Message'),
        ('photo', 'Photo'),
        ('document', 'Document'),
        ('inline_keyboard', 'Inline Keyboard'),
        ('multi_message', 'Multi Message'),
    ], string='Reply Type', default='text')
    
    reply_keyboard = fields.Text(
        string='Inline Keyboard',
        help='JSON configuration for inline keyboard buttons'
    )
    
    # Conditions
    is_active = fields.Boolean(
        string='Active',
        default=True
    )
    
    requires_auth = fields.Boolean(
        string='Requires Authentication',
        default=False,
        help='User must be linked to an Odoo user'
    )
    
    requires_admin = fields.Boolean(
        string='Requires Admin',
        default=False,
        help='Only bot admins can use this command'
    )
    
    allowed_user_ids = fields.Many2many(
        'telegram.bot.user',
        string='Allowed Users',
        help='Specific users allowed to use this command'
    )
    
    # Arguments
    accepts_arguments = fields.Boolean(
        string='Accepts Arguments',
        default=False
    )
    
    argument_description = fields.Char(
        string='Argument Description',
        help='Description of expected arguments'
    )
    
    argument_example = fields.Char(
        string='Example',
        help='Example usage with arguments'
    )
    
    # Statistics
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True
    )
    
    last_used = fields.Datetime(
        string='Last Used',
        readonly=True
    )
    
    # Relations
    bot_id = fields.Many2one(
        'telegram.bot',
        string='Bot',
        required=True,
        ondelete='cascade'
    )
    
    # Sequence
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in command list'
    )
    
    # Metadata
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='bot_id.company_id',
        store=True
    )

    # ==================== Computed Fields ====================
    
    @api.depends('name')
    def _compute_full_command(self):
        """Compute full command with slash"""
        for cmd in self:
            cmd.full_command = f'/{cmd.name}'

    # ==================== Constraints ====================
    
    _sql_constraints = [
        ('unique_command_per_bot',
         'UNIQUE(bot_id, name)',
         'This command already exists for this bot!'),
    ]

    @api.constrains('name')
    def _check_command_name(self):
        """Validate command name"""
        for cmd in self:
            if cmd.name:
                # Remove slash if present
                if cmd.name.startswith('/'):
                    cmd.name = cmd.name[1:]
                
                # Check for invalid characters
                if ' ' in cmd.name:
                    raise ValidationError(_('Command name cannot contain spaces.'))
                
                # Check length
                if len(cmd.name) > 32:
                    raise ValidationError(_('Command name is too long (max 32 characters).'))

    @api.constrains('custom_action')
    def _check_custom_action(self):
        """Validate custom action code"""
        for cmd in self:
            if cmd.action == 'custom' and cmd.custom_action:
                # Basic security check - prevent dangerous operations
                dangerous_patterns = ['exec', 'eval', '__import__', 'open', 'os.system', 'subprocess']
                code_lower = cmd.custom_action.lower()
                for pattern in dangerous_patterns:
                    if pattern in code_lower:
                        raise ValidationError(_(
                            'Custom action contains unsafe code pattern: %s' % pattern
                        ))

    # ==================== Action Methods ====================
    
    def action_execute(self, chat_id, args=None, user_id=None):
        """
        Execute command and return response
        
        Args:
            chat_id: Telegram chat ID
            args: Command arguments
            user_id: Telegram user record ID
            
        Returns:
            dict: Response data with message and keyboard
        """
        self.ensure_one()
        
        # Update statistics
        self.usage_count += 1
        self.last_used = fields.Datetime.now()
        
        # Check permissions
        if self.requires_admin and user_id:
            user = self.env['telegram.bot.user'].browse(user_id)
            if not user.is_admin:
                return {
                    'text': '⛔ This command is only available for administrators.',
                    'type': 'text'
                }
        
        # Execute based on action type
        if self.action == 'custom':
            return self._execute_custom(chat_id, args, user_id)
        else:
            return self._execute_builtin(chat_id, args, user_id)

    def _execute_builtin(self, chat_id, args, user_id):
        """Execute built-in command actions"""
        self.ensure_one()
        
        if self.action == 'start':
            return self._handle_start(chat_id, user_id)
        elif self.action == 'help':
            return self._handle_help(chat_id)
        elif self.action == 'order_status':
            return self._handle_order_status(chat_id, args, user_id)
        elif self.action == 'invoice_status':
            return self._handle_invoice_status(chat_id, args, user_id)
        elif self.action == 'product_search':
            return self._handle_product_search(chat_id, args)
        elif self.action == 'contact_info':
            return self._handle_contact_info(chat_id)
        elif self.action == 'business_hours':
            return self._handle_business_hours(chat_id)
        else:
            return {
                'text': self.reply_template or 'Command not implemented.',
                'type': 'text'
            }

    def _handle_start(self, chat_id, user_id):
        """Handle /start command"""
        welcome_text = f"""
Welcome to {self.bot_id.name}! 👋

I can help you with:

📦 */order_status* - Check your orders
💰 */invoice_status* - Check invoices
🔍 */product_search* - Search products
📊 */account_summary* - Account summary
🆘 */support* - Get help

Type */help* to see all available commands.
        """
        return {
            'text': welcome_text,
            'type': 'text'
        }

    def _handle_help(self, chat_id):
        """Handle /help command"""
        help_text = f"*Available Commands for {self.bot_id.name}:*\n\n"
        
        commands = self.env['telegram.command'].search([
            ('bot_id', '=', self.bot_id.id),
            ('is_active', '=', True)
        ], order='sequence')
        
        for cmd in commands:
            example = f" {cmd.argument_example}" if cmd.argument_example else ""
            help_text += f"/{cmd.name}{example} - {cmd.description}\n"
        
        return {
            'text': help_text,
            'type': 'text'
        }

    def _handle_order_status(self, chat_id, args, user_id):
        """Handle /order_status command"""
        if not args:
            # Show recent orders
            return self._get_recent_orders(chat_id, user_id)
        else:
            # Search specific order
            order_ref = args[0] if isinstance(args, list) else args
            return self._get_order_details(order_ref)

    def _handle_invoice_status(self, chat_id, args, user_id):
        """Handle /invoice_status command"""
        if not args:
            return self._get_recent_invoices(chat_id, user_id)
        else:
            invoice_ref = args[0] if isinstance(args, list) else args
            return self._get_invoice_details(invoice_ref)

    def _execute_custom(self, chat_id, args, user_id):
        """Execute custom command"""
        self.ensure_one()
        
        try:
            if self.custom_handler:
                # Call specified method
                model_name, method = self.custom_handler.rsplit('.', 1)
                result = self.env[model_name].sudo()[method](
                    chat_id=chat_id, args=args, user_id=user_id, command=self
                )
                return result
            elif self.custom_action:
                # Execute custom code in safe environment
                local_vars = {
                    'chat_id': chat_id,
                    'args': args,
                    'user_id': user_id,
                    'command': self,
                    'env': self.env,
                    'result': {'text': '', 'type': 'text'}
                }
                safe_globals = {
                    '__builtins__': {
                        'str': str, 'int': int, 'float': float,
                        'list': list, 'dict': dict, 'bool': bool,
                        'len': len, 'range': range, 'print': print,
                    }
                }
                exec(self.custom_action, safe_globals, local_vars)
                return local_vars.get('result', {'text': 'Command executed.', 'type': 'text'})
            else:
                return {'text': 'Custom action not configured.', 'type': 'text'}
        except Exception as e:
            _logger.error(f"Custom command error: {e}")
            return {'text': f'Error executing command: {str(e)}', 'type': 'text'}