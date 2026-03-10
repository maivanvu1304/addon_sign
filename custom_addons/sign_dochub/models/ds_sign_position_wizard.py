from odoo import models, fields, api
import json


class DsSignPositionWizard(models.TransientModel):
    _name = 'ds.sign.position.wizard'
    _description = 'Sign Position Wizard'

    document_id = fields.Many2one('ds.document', string='Document', required=True)
    attachment_id = fields.Many2one('ir.attachment', string='File PDF')
    position_data = fields.Text(string='Position Data (JSON)')  # lưu tọa độ từ frontend

    def action_save_positions(self):
        """Save signature positions from frontend JSON data to request items"""
        self.ensure_one()
        if self.position_data:
            data = json.loads(self.position_data)
            for item_data in data:
                item = self.env['ds.document.request.item'].browse(item_data['item_id'])
                if item.exists():
                    item.write({
                        'signature_pos_x': item_data.get('x', 0),
                        'signature_pos_y': item_data.get('y', 0),
                        'page_number': item_data.get('page', 1),
                    })
        return {'type': 'ir.actions.act_window_close'}