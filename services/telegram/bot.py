import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import redis
import odoorpc
import os
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger.info(f"Telegram bot token loaded: {bool(TOKEN)}")

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ODOO_URL = os.getenv('ODOO_URL', 'http://odoo:8069')
ODOO_DB = os.getenv('ODOO_DB', 'erp_db')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379')

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Odoo connection
class OdooConnector:
    def __init__(self):
        self.odoo = None
        
    def connect(self):
        try:
            self.odoo = odoorpc.ODOO(ODOO_URL.replace('http://', '').replace('https://', ''), port=8069)
            self.odoo.login(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
            logger.info("Connected to Odoo")
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
    
    def search_read(self, model, domain, fields=None, limit=None):
        if not self.odoo:
            self.connect()
        try:
            return self.odoo.execute(model, 'search_read', domain, fields or [], limit or 0)
        except Exception as e:
            logger.error(f"Odoo search_read error: {e}")
            self.connect()  # Reconnect and retry
            return self.odoo.execute(model, 'search_read', domain, fields or [], limit or 0)

odoo = OdooConnector()

# Redis connection
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    user = update.effective_user
    welcome_message = f"""
Hello {user.first_name}! 👋

Welcome to ERP Bot. I can help you with:

📦 */order_status* - Check your orders
💰 */invoice_status* - Check invoices
🔍 */product_search* - Search products
📊 */account_summary* - Your account summary
🆘 */support* - Get help
🎁 */offers* - Latest offers

Type /help to see all available commands.
    """
    
    keyboard = [
        [InlineKeyboardButton("📦 My Orders", callback_data='my_orders')],
        [InlineKeyboardButton("💰 My Invoices", callback_data='my_invoices')],
        [InlineKeyboardButton("🆘 Support", callback_data='support')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
*Available Commands:*

📦 */order_status [number]* - Check order status
💰 */invoice_status [number]* - Check invoice status  
🔍 */product_search [keyword]* - Search products
📊 */account_summary* - Your account overview
🎁 */offers* - Latest promotions
🆘 */support* - Contact support
📞 */contact* - Company contact info
🕐 */hours* - Business hours

You can also just type your question and I'll help!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check order status"""
    try:
        if context.args:
            order_ref = context.args[0]
            orders = odoo.search_read('sale.order', [
                ('name', '=', order_ref)
            ], ['name', 'state', 'amount_total', 'expected_date', 'delivery_status'])
            
            if orders:
                order = orders[0]
                response = f"""
*Order: {order['name']}*

Status: {order['state']}
Total: Rp {order['amount_total']:,.2f}
Expected: {order.get('expected_date', 'TBD')}
Delivery: {order.get('delivery_status', 'Pending')}

Track online: {ODOO_URL}/my/orders/{order['id']}
                """
            else:
                response = f"❌ Order {order_ref} not found"
        else:
            # Show recent orders
            orders = odoo.search_read('sale.order', [
                ('state', 'not in', ['draft', 'cancel'])
            ], ['name', 'state', 'amount_total'], limit=5)
            
            if orders:
                response = "*Your Recent Orders:*\n\n"
                for order in orders:
                    response += f"📦 {order['name']} - {order['state']} (Rp {order['amount_total']:,.2f})\n"
            else:
                response = "You have no orders yet"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Order status error: {e}")
        await update.message.reply_text("❌ Error fetching orders. Please try again.")

async def product_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search products"""
    query = ' '.join(context.args) if context.args else ''
    
    if not query:
        await update.message.reply_text("Please provide a search term. Example: /product_search laptop")
        return
    
    try:
        products = odoo.search_read('product.product', [
            ('name', 'ilike', query),
            ('sale_ok', '=', True)
        ], ['name', 'list_price', 'qty_available', 'image_128'], limit=5)
        
        if products:
            response = f"*Search results for '{query}':*\n\n"
            for product in products:
                response += f"📦 {product['name']}\n"
                response += f"   💰 Rp {product['list_price']:,.2f}\n"
                response += f"   📊 Stock: {product['qty_available']} units\n\n"
        else:
            response = f"❌ No products found for '{query}'"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Product search error: {e}")
        await update.message.reply_text("❌ Error searching products")

async def invoice_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check invoice status"""
    try:
        if context.args:
            invoice_ref = context.args[0]
            invoices = odoo.search_read('account.move', [
                ('name', '=', invoice_ref),
                ('move_type', 'in', ['out_invoice', 'out_refund'])
            ], ['name', 'amount_total', 'amount_residual', 'invoice_date_due', 'payment_state'])
            
            if invoices:
                invoice = invoices[0]
                response = f"""
*Invoice: {invoice['name']}*

Amount: Rp {invoice['amount_total']:,.2f}
Remaining: Rp {invoice['amount_residual']:,.2f}
Due Date: {invoice.get('invoice_date_due', 'N/A')}
Status: {invoice['payment_state']}

Pay online: {ODOO_URL}/my/invoices/{invoice['id']}
                """
            else:
                response = f"❌ Invoice {invoice_ref} not found"
        else:
            # Show recent invoices
            invoices = odoo.search_read('account.move', [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], ['name', 'amount_total', 'payment_state'], limit=5)
            
            if invoices:
                response = "*Your Recent Invoices:*\n\n"
                for inv in invoices:
                    status_emoji = "✅" if inv['payment_state'] == 'paid' else "⚠️"
                    response += f"{status_emoji} {inv['name']} - Rp {inv['amount_total']:,.2f}\n"
            else:
                response = "You have no invoices yet"
        
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Invoice status error: {e}")
        await update.message.reply_text("❌ Error fetching invoices")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'my_orders':
        await order_status(update, context)
    elif query.data == 'my_invoices':
        await invoice_status(update, context)
    elif query.data == 'support':
        await query.edit_message_text(
            "📞 *Contact Support*\n\n"
            "Email: support@yourcompany.com\n"
            "Phone: +62xxx\n"
            "Hours: Mon-Fri 9AM-5PM\n\n"
            "Please describe your issue and we'll help you!",
            parse_mode='Markdown'
        )

def main():
    """Start the bot"""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("order_status", order_status))
    application.add_handler(CommandHandler("invoice_status", invoice_status))
    application.add_handler(CommandHandler("product_search", product_search))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler for non-command messages
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_message
    ))
    
    # Start the Bot
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages"""
    message_text = update.message.text.lower()
    
    # Simple NLP-like responses
    if any(word in message_text for word in ['hello', 'hi', 'hey']):
        await start(update, context)
    elif 'order' in message_text:
        await order_status(update, context)
    elif 'invoice' in message_text:
        await invoice_status(update, context)
    elif 'product' in message_text:
        # Extract potential search terms
        query = message_text.replace('product', '').replace('search', '').strip()
        if query:
            context.args = [query]
            await product_search(update, context)
        else:
            await update.message.reply_text("What product are you looking for?")
    else:
        # Forward to support or provide general help
        keyboard = [
            [InlineKeyboardButton("📦 Check Orders", callback_data='my_orders')],
            [InlineKeyboardButton("💰 Check Invoices", callback_data='my_invoices')],
            [InlineKeyboardButton("🆘 Contact Support", callback_data='support')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "I'm not sure what you mean. Here are some things I can help with:",
            reply_markup=reply_markup
        )

if __name__ == '__main__':
    main()
