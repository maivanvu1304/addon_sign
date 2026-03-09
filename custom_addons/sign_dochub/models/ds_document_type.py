from odoo import models, fields


class DsDocumentType(models.Model):
    _name = 'ds.document.type'
    _description = 'Document Type'

    name = fields.Char(string='Document Type Name', required=True)
    code = fields.Char(string='Code')
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Sequence',
    )
    default_template_id = fields.Many2one(
        'ds.document.template',
        string='Default Template',
    )
