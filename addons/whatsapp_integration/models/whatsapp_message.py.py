from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class WhatsAppMessage(models.Model):
    _name = 'whatsapp.message'
    _description = 'WhatsApp Message'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Subject', required=True)
    message_type = fields.Selection([
        ('text', 'Text'),
        ('template', 'Template'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('location', 'Location'),
        ('order_update', 'Order Update'),
        ('invoice', 'Invoice'),
        ('payment_reminder', 'Payment Reminder'),
    ], string='Message Type', default='text', required=True)
    
    recipient_number = fields.Char(string='Recipient Number', required=True)
    message_body = fields.Text(string='Message Body')
    
    partner_id = fields.Many2one('res.partner', string='Customer')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('queued', 'Queued'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', tracking=True)
    
    response_data = fields.Text(string='Response Data')
    error_message = fields.Text(string='Error Message')
    
    def send_message(self):
        """Send WhatsApp message via service"""
        for record in self:
            try:
                record.state = 'queued'
                
                # Prepare message payload
                payload = {
                    'message_id': record.id,
                    'recipient': record.recipient_number,
                    'type': record.message_type,
                    'content': record._prepare_message_content(),
                }
                
                # Send to WhatsApp service via Redis queue or direct API
                # This will be picked up by the WhatsApp service
                self.env['whatsapp.queue'].create({
                    'message_id': record.id,
                    'payload': json.dumps(payload),
                    'state': 'pending'
                })
                
                record.message_post(body=f"WhatsApp message queued for {record.recipient_number}")
                
            except Exception as e:
                record.state = 'failed'
                record.error_message = str(e)
                _logger.error(f"Failed to send WhatsApp message: {e}")
    
    def _prepare_message_content(self):
        """Prepare message content based on type"""
        if self.message_type == 'order_update' and self.sale_order_id:
            return self._prepare_order_update()
        elif self.message_type == 'invoice' and self.invoice_id:
            return self._prepare_invoice_message()
        elif self.message_type == 'payment_reminder' and self.invoice_id:
            return self._prepare_payment_reminder()
        return self.message_body
    
    def _prepare_order_update(self):
        """Prepare order update message"""
        order = self.sale_order_id
        return f"""
        *Order Update #{order.name}*
        
        Status: {order.state}
        Total: Rp {order.amount_total:,.2f}
        Delivery: {order.expected_date or 'TBD'}
        
        Track your order: {order.get_portal_url()}
        """
    
    def _prepare_invoice_message(self):
        """Prepare invoice message"""
        invoice = self.invoice_id
        return f"""
        *Invoice {invoice.name}*
        
        Amount: Rp {invoice.amount_total:,.2f}
        Due Date: {invoice.invoice_date_due}
        
        Pay now: {invoice.get_portal_url()}
        """
    
    def _prepare_payment_reminder(self):
        """Prepare payment reminder"""
        invoice = self.invoice_id
        return f"""
        *Payment Reminder*
        
        Invoice: {invoice.name}
        Amount Due: Rp {invoice.amount_residual:,.2f}
        Due Date: {invoice.invoice_date_due}
        
        Please pay before the due date to avoid late fees.
        Pay now: {invoice.get_portal_url()}
        """