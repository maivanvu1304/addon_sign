from odoo import models, fields


class DsDocumentTemplate(models.Model):
    _name = 'ds.document.template'
    _description = 'Document Template'

    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    step_ids = fields.One2many(
        'ds.document.template.step',
        'template_id',
        string='Steps',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
    )


class DsDocumentTemplateStep(models.Model):
    _name = 'ds.document.template.step'
    _description = 'Document Template Step'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        'ds.document.template',
        string='Template',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Step Name', required=True)
    role = fields.Selection(
        selection=[
            ('sign', 'Sign'),
            ('approve', 'Approve'),
        ],
        string='Role',
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
    )
    is_external = fields.Boolean(string='External Signer', default=False)
    partner_id = fields.Many2one(
        'res.partner',
        string='External Partner',
    )
