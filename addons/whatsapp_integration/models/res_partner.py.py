from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    whatsapp_number = fields.Char(string='WhatsApp Number')
    whatsapp_opt_out = fields.Boolean(string='WhatsApp Opt-out')
    whatsapp_last_message_date = fields.Datetime(string='Last WhatsApp Message')
    
    # Automated notifications
    whatsapp_order_confirmation = fields.Boolean(
        string='Send Order Confirmation', default=True)
    whatsapp_shipping_update = fields.Boolean(
        string='Send Shipping Updates', default=True)
    whatsapp_invoice_notification = fields.Boolean(
        string='Send Invoice Notification', default=True)
    whatsapp_payment_reminder = fields.Boolean(
        string='Send Payment Reminder', default=True)