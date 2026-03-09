import random
import string

from odoo import models, fields, api


class DsDocumentCustomer(models.Model):
    _name = 'ds.document.customer'
    _description = 'Document Customer'

    document_id = fields.Many2one(
        'ds.document',
        string='Document',
        required=True,
        ondelete='cascade',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    email = fields.Char(
        string='Email',
        store=True,
        readonly=False,
    )
    phone = fields.Char(
        string='Phone',
        related='partner_id.phone',
    )
    verification_code = fields.Char(
        string='Verification Code',
        default=lambda self: self._generate_code(),
        copy=False,
    )
    is_sent = fields.Boolean(string='Is Sent', default=False)
    date_sent = fields.Datetime(string='Date Sent')

    @api.model
    def _generate_code(self):
        """Generate random 6-character verification code"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choices(chars, k=6))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.email = self.partner_id.email

    def action_send_customer_email(self):
        """Send notification email to customer (placeholder)"""
        self.write({
            'is_sent': True,
            'date_sent': fields.Datetime.now(),
        })

    def action_preview(self):
        """Preview document as customer would see it (placeholder)"""
        pass
