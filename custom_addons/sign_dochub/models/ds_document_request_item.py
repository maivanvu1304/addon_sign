import uuid

from odoo import models, fields, api


class DsDocumentRequestItem(models.Model):
    _name = 'ds.document.request.item'
    _description = 'Document Request Item'
    _order = 'sequence, id'

    document_id = fields.Many2one(
        'ds.document',
        string='Document',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Step Name')
    role = fields.Selection(
        selection=[
            ('sign', 'Ký số'),
            ('approve', 'Phê duyệt'),
        ],
        string='Role',
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
    )
    email = fields.Char(
        string='Email',
    )
    phone = fields.Char(
        string='Phone',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        default='draft',
    )
    date_sent = fields.Datetime(string='Date Sent')
    date_action = fields.Datetime(string='Date Action')
    transaction_id = fields.Char(string='Transaction ID')
    document_hash = fields.Char(string='Document Hash')
    note = fields.Text(string='Note')
    access_token = fields.Char(
        string='Access Token',
        copy=False,
        default=lambda self: str(uuid.uuid4()),
    )
    is_current_user = fields.Boolean(
        string='Is Current User',
        compute='_compute_is_current_user',
    )
    # Phase 2 fields
    signature_pos_x = fields.Float(string='Signature Position X')
    signature_pos_y = fields.Float(string='Signature Position Y')
    page_number = fields.Integer(string='Page Number', default=1)

    @api.depends_context('uid')
    def _compute_is_current_user(self):
        for item in self:
            item.is_current_user = item.user_id.id == self.env.uid

    def action_approve(self):
        """Approve/Sign this step"""
        self.write({
            'state': 'done',
            'date_action': fields.Datetime.now(),
        })
        for item in self:
            item.document_id._activate_next_step()

    def action_reject(self):
        """Reject this step"""
        self.write({
            'state': 'rejected',
            'date_action': fields.Datetime.now(),
        })
        for item in self:
            item.document_id.write({'state': 'rejected'})
            item.document_id.message_post(
                body=f"Step '{item.name}' rejected by {item.user_id.name}. Note: {item.note or ''}",
                message_type='notification',
            )

    def _send_notification_email(self):
        """Send email notification to signer (placeholder for mail template)"""
        pass
