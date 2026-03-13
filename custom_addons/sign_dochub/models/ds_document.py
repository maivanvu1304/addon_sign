from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

SIGNED_NOTE_PREFIX = 'Đã ký bằng tên: '


class DsDocument(models.Model):
    _name = 'ds.document'
    _description = 'Document'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'
    _rec_name = 'name'

    # Group A — Document Information
    name = fields.Char(
        string='Document Code',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    title = fields.Char(string='Tiêu đề chứng từ', required=True)
    description = fields.Text(string='Mô tả')
    document_type_id = fields.Many2one(
        'ds.document.type',
        string='Loại chứng từ',
        required=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Bộ phận',
    )
    related_document_id = fields.Many2one(
        'ds.document',
        string='Chứng từ liên quan',
    )
    coordinator_id = fields.Many2one(
        'res.users',
        string='Người điều phối',
    )
    viewer_ids = fields.Many2many(
        'res.users',
        'ds_document_viewer_rel',
        'document_id',
        'user_id',
        string='Người xem',
    )

    # Group B — Document Files
    attachment_id = fields.Many2many(
        'ir.attachment',
        'ds_document_attachment_rel',
        'document_id',
        'attachment_id',
        string='File gốc',
        required=True,
    )
    signed_attachment_id = fields.Many2one(
        'ir.attachment',
        string='File đã ký',
    )
    related_attachment_ids = fields.Many2many(
        'ir.attachment',
        'ds_document_related_attachment_rel',
        'document_id',
        'attachment_id',
        string='Tài liệu liên quan',
    )
    password = fields.Char(string='File Password')
    auto_sign_position = fields.Selection(
        selection=[
            ('above', 'Trên chữ ký'),
            ('below', 'Dưới chữ ký'),
            ('custom', 'Tùy chỉnh'),
        ],
        string='Vị trí ký',
    )
    render_mode = fields.Selection(
        selection=[
            ('signature_only', 'Chỉ hiển thị chữ ký'),
            ('full', 'Hiển thị toàn bộ'),
        ],
        string='Chế độ hiển thị',
    )

    # Group C — Time & Customer Information
    date_deadline = fields.Date(string='Ngày hết hạn xử lý')
    date_effective_from = fields.Date(string='Ngày có hiệu lực')
    date_effective_to = fields.Date(string='Ngày hết hiệu lực')
    partner_id = fields.Many2one(
        'res.partner',
        string='Khách hàng',
    )
    contract_value = fields.Monetary(string='Giá trị hợp đồng')
    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        default=lambda self: self.env.company.currency_id,
    )

    # Group D — Workflow & System
    position_confirmed = fields.Boolean(
        string='Đã chốt vị trí ký',
        default=False,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Chứng từ mới'),
            ('in_progress', 'Đang xử lý'),
            ('adjusting', 'Đang điều chỉnh'),
            ('done', 'Đã hoàn tất'),
            ('rejected', 'Từ chối'),
            ('cancelled', 'Đã hủy'),
        ],
        string='Trạng thái',
        default='draft',
        tracking=True,
    )
    template_id = fields.Many2one(
        'ds.document.template',
        string='Workflow Template',
    )
    request_item_ids = fields.One2many(
        'ds.document.request.item',
        'document_id',
        string='Request Items',
    )
    customer_ids = fields.One2many(
        'ds.document.customer',
        'document_id',
        string='Customer Notifications',
    )
    creator_id = fields.Many2one(
        'res.users',
        string='Creator',
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
    )
    date_request = fields.Datetime(string='Request Date')
    date_done = fields.Datetime(string='Completion Date')
    cancel_reason = fields.Text(string='Cancel Reason')
    cancel_user_id = fields.Many2one(
        'res.users',
        string='Cancelled By',
    )
    cancel_date = fields.Datetime(string='Cancel Date')

    # Computed fields
    current_signer_id = fields.Many2one(
        'res.users',
        string='Current Signer',
        compute='_compute_current_signer',
    )
    current_signer_state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('rejected', 'Rejected'),
            ('cancelled', 'Cancelled'),
        ],
        string='Current Step State',
        compute='_compute_current_signer',
    )
    current_signer_role = fields.Selection(
        selection=[
            ('sign', 'Ký số'),
            ('approve', 'Phê duyệt'),
        ],
        string='Current Signer Role',
        compute='_compute_current_signer',
    )
    item_count = fields.Integer(
        string='Total Steps',
        compute='_compute_item_count',
    )
    item_done_count = fields.Integer(
        string='Completed Steps',
        compute='_compute_item_count',
    )

    attachment_count = fields.Integer(
        string='Files',
        compute='_compute_attachment_count'
    )

    # Đếm số lịch sử ký
    sign_history_count = fields.Integer(
        string='Lịch sử ký',
        compute='_compute_sign_history_count'
    )
    
    sign_positions_set = fields.Boolean(
        string='Đã đặt vị trí ký',
        compute='_compute_sign_positions_set',
        help='True khi tất cả bước ký đã có tọa độ vị trí hợp lệ',
    )
    can_finish_sign_step = fields.Boolean(
        string='Can Finish Sign Step',
        compute='_compute_can_finish_sign_step',
        help='True khi có thể bấm nút Hoàn tất ký để chuyển sang bước kế tiếp',
    )
    can_request_resign = fields.Boolean(
        string='Can Request Resign',
        compute='_compute_can_request_resign',
        help='True khi có thể yêu cầu bước ký trước đó ký lại',
    )

    @api.depends(
        'request_item_ids',
        'request_item_ids.signature_pos_x',
        'request_item_ids.signature_pos_y',
        'request_item_ids.page_number',
    )
    def _compute_sign_positions_set(self):
        """
        True khi:
          - Có ít nhất 1 request item
          - Với các bước cần ký (role != approve), phải có tọa độ ký khác 0
        """
        for doc in self:
            items = doc.request_item_ids
            if not items:
                doc.sign_positions_set = False
                continue
            sign_items = items.filtered(lambda item: item.role != 'approve')
            if not sign_items:
                doc.sign_positions_set = True
                continue
            doc.sign_positions_set = all(
                (item.signature_pos_x or 0) != 0 or (item.signature_pos_y or 0) != 0
                for item in sign_items
            )
    @api.depends('attachment_id', 'related_attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            if rec.state != 'draft':
                rec.attachment_count = len(rec.attachment_id)
            else:
                rec.attachment_count = 0

    @api.depends()  # thay bằng field liên quan nếu có
    def _compute_sign_history_count(self):
        for rec in self:
            rec.sign_history_count = self.env['mail.message'].search_count([
                ('res_id', '=', rec.id),
                ('model', '=', 'ds.document'),
                ('message_type', '=', 'notification'),
            ])

    # ==================== Computed Methods ====================

    @api.depends('request_item_ids', 'request_item_ids.state', 'request_item_ids.user_id', 'request_item_ids.role')
    def _compute_current_signer(self):
        for doc in self:
            current_item = doc.request_item_ids.filtered(
                lambda i: i.state == 'pending'
            )[:1]
            doc.current_signer_id = current_item.user_id if current_item else False
            doc.current_signer_state = current_item.state if current_item else False
            doc.current_signer_role = current_item.role if current_item else False

    @api.depends('request_item_ids', 'request_item_ids.state')
    def _compute_item_count(self):
        for doc in self:
            doc.item_count = len(doc.request_item_ids)
            doc.item_done_count = len(doc.request_item_ids.filtered(
                lambda i: i.state == 'done'
            ))

    @api.depends('state', 'position_confirmed', 'request_item_ids', 'request_item_ids.state', 'request_item_ids.note')
    def _compute_can_finish_sign_step(self):
        for doc in self:
            pending_items = doc.request_item_ids.filtered(lambda i: i.state == 'pending')
            has_pending = bool(pending_items)
            has_signed_pending = any(
                (item.note or '').startswith(SIGNED_NOTE_PREFIX)
                for item in pending_items
            )
            has_done = any(item.state == 'done' for item in doc.request_item_ids)
            doc.can_finish_sign_step = (
                doc.state == 'adjusting'
                and doc.position_confirmed
                and bool(doc.request_item_ids)
                and (has_signed_pending or (has_done and not has_pending))
            )

    @api.depends('state', 'position_confirmed', 'request_item_ids', 'request_item_ids.state', 'request_item_ids.sequence')
    def _compute_can_request_resign(self):
        for doc in self:
            doc.can_request_resign = False
            if doc.state != 'adjusting' or not doc.position_confirmed:
                continue

            ordered_items = doc.request_item_ids.sorted(lambda i: (i.sequence, i.id))
            pending_index = next(
                (idx for idx, item in enumerate(ordered_items) if item.state == 'pending'),
                None,
            )
            doc.can_request_resign = pending_index is not None and pending_index > 0

    # ==================== CRUD ====================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ds.document') or 'New'
        return super().create(vals_list)

    # ==================== Workflow Actions ====================

    def action_start_workflow(self):
        """Button [Khởi tạo quy trình]: Validate → in_progress"""
        for doc in self:
            if not doc.request_item_ids:
                raise UserError("Please add at least one workflow step before starting.")
            doc.write({
                'state': 'in_progress',
                'date_request': fields.Datetime.now(),
            })

    def action_adjust(self):
        """Button [Đặt vị trí ký]: Switch to adjusting state"""
        self.write({'state': 'adjusting', 'position_confirmed': False})

    def action_reset_positions(self):
        """Button [Reset vị trí ký]: Clear signature positions"""
        self.request_item_ids.write({
            'signature_pos_x': 0,
            'signature_pos_y': 0,
            'page_number': 1,
        })

    def action_send_sign_request(self):
        """Mở UI để người đầu tiên thực hiện ký"""
        self.ensure_one()
        if not self.attachment_id:
            raise UserError("Vui lòng đính kèm tệp chứng từ trước khi ký.")

        pending_item = self.request_item_ids.filtered(
            lambda i: i.state == 'pending'
        ).sorted('sequence')[:1]
        if pending_item and pending_item.role == 'approve':
            raise UserError(
                'Bước hiện tại là phê duyệt. Vui lòng bấm "Duyệt" để chuyển sang bước tiếp theo.'
            )
        if pending_item and (pending_item.note or '').startswith(SIGNED_NOTE_PREFIX):
            raise UserError(
                'Bước ký hiện tại đã ký xong. Vui lòng bấm "Hoàn tất ký" để chuyển sang bước tiếp theo.'
            )
        if not pending_item:
            draft_items = self.request_item_ids.filtered(lambda i: i.state == 'draft')
            done_items = self.request_item_ids.filtered(lambda i: i.state == 'done')
            if done_items and draft_items:
                raise UserError(
                    'Bước ký hiện tại đã hoàn tất. Vui lòng bấm "Hoàn tất ký" để chuyển sang bước tiếp theo.'
                )
            if done_items and not draft_items:
                raise UserError(
                    'Tất cả bước ký đã hoàn tất. Vui lòng bấm "Hoàn tất ký" để kết thúc chứng từ.'
                )
            raise UserError(
                'Chưa có bước ký nào ở trạng thái chờ. Vui lòng kiểm tra lại quy trình ký.'
            )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'ds_sign_document',
            'target': 'main',
            'context': {
                'document_id': self.id,
            },
            'name': 'Ký chứng từ',
        }

    def action_finish_sign_step(self):
        """
        Button [Hoàn tất ký]:
        - Luồng mới: pending đã ký (ghi note) -> done -> kích hoạt bước kế
        - Luồng cũ tương thích: không còn pending nhưng có done -> kích hoạt bước kế
        """
        for doc in self:
            if doc.state != 'adjusting' or not doc.position_confirmed:
                raise UserError(
                    "Chỉ có thể hoàn tất ký khi chứng từ đang ở trạng thái Điều chỉnh và đã gửi quy trình."
                )

            pending_item = doc.request_item_ids.filtered(
                lambda i: i.state == 'pending'
            ).sorted('sequence')[:1]
            if pending_item:
                if pending_item.role == 'approve':
                    raise UserError(
                        'Bước hiện tại là phê duyệt. Vui lòng bấm "Duyệt" để chuyển sang bước tiếp theo.'
                    )
                if not (pending_item.note or '').startswith(SIGNED_NOTE_PREFIX):
                    raise UserError(
                        "Bước ký hiện tại chưa hoàn tất. Vui lòng vào màn ký để ký trước."
                    )
                pending_item.action_approve()
                doc._activate_next_step()
                continue

            if not doc.request_item_ids.filtered(lambda i: i.state == 'done'):
                raise UserError(
                    "Chưa có bước ký nào hoàn tất để chuyển sang bước tiếp theo."
                )
            doc._activate_next_step()

    def action_approve_step(self):
        """
        Button [Duyệt]:
        - Chỉ dùng cho bước pending có role = 'approve'
        - Xác nhận bước hiện tại và chuyển sang bước kế tiếp
        """
        for doc in self:
            if doc.state != 'adjusting' or not doc.position_confirmed:
                raise UserError(
                    "Chỉ có thể duyệt khi chứng từ đang ở trạng thái Điều chỉnh và đã gửi quy trình."
                )

            pending_item = doc.request_item_ids.filtered(
                lambda i: i.state == 'pending'
            ).sorted('sequence')[:1]
            if not pending_item:
                raise UserError("Không có bước nào đang chờ để duyệt.")
            if pending_item.role != 'approve':
                raise UserError("Bước hiện tại không phải loại Phê duyệt.")

            pending_item.action_approve()
            doc._activate_next_step()

    def action_reject_document(self):
        """Button [Từ chối]: Change state to rejected"""
        self.write({'state': 'rejected'})
        self.request_item_ids.filtered(
            lambda i: i.state not in ('done', 'cancelled', 'rejected')
        ).write({'state': 'rejected'})

    def action_publish(self):
        """Button [Ban hành kết quả]: Send email to all customers"""
        for doc in self:
            if not doc.customer_ids:
                raise ValidationError("Vui lòng thêm khách hàng trong tab Quy trình khách hàng trước khi ban hành kết quả.")
            for customer in doc.customer_ids:
                customer.action_send_customer_email()

    def action_request_resign(self):
        """Button [Yêu cầu ký lại]: chỉ yêu cầu bước ngay trước bước đang chờ ký ký lại"""
        for doc in self:
            ordered_items = doc.request_item_ids.sorted(lambda i: (i.sequence, i.id))
            pending_index = next(
                (idx for idx, item in enumerate(ordered_items) if item.state == 'pending'),
                None,
            )

            if pending_index is None:
                raise UserError("Không có bước nào đang chờ ký để yêu cầu ký lại.")
            if pending_index == 0:
                raise UserError("Bước đầu tiên không thể yêu cầu ký lại.")

            items_to_reset = ordered_items[pending_index - 1:]
            items_to_reset.write({
                'state': 'draft',
                'date_action': False,
                'date_sent': False,
                'note': False,
            })
            doc.write({'position_confirmed': True})
            doc._activate_next_step()

    def action_cancel(self):
        """Cancel document — in production, opens wizard for reason"""
        self.write({'state': 'cancelled'})
        self.request_item_ids.filtered(
            lambda i: i.state not in ('done', 'cancelled')
        ).write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.write({'state': 'draft', 'position_confirmed': False})
        self.request_item_ids.write({
            'state': 'draft',
            'date_action': False,
            'date_sent': False,
            'note': False,
        })

    def action_share(self):
        """Button [Chia sẻ tài liệu]: Generate portal link (placeholder)"""
        pass

    def apply_template(self):
        """Button [Tải quy trình]: Apply template steps to this document"""
        for doc in self:
            if not doc.template_id:
                raise UserError("Please select a workflow template first.")
            # Remove existing draft items
            doc.request_item_ids.filtered(lambda i: i.state == 'draft').unlink()
            # Create items from template steps
            for step in doc.template_id.step_ids:
                self.env['ds.document.request.item'].create({
                    'document_id': doc.id,
                    'sequence': step.sequence,
                    'name': step.name,
                    'role': step.role,
                    'user_id': step.user_id.id if step.user_id else False,
                    'partner_id': step.partner_id.id if step.partner_id else False,
                })

    def save_as_template(self):
        """Button [Lưu mẫu quy trình]: Save current config as template"""
        for doc in self:
            template = self.env['ds.document.template'].create({
                'name': f"Template from {doc.name}",
                'company_id': doc.company_id.id,
            })
            for item in doc.request_item_ids:
                self.env['ds.document.template.step'].create({
                    'template_id': template.id,
                    'sequence': item.sequence,
                    'name': item.name or f"Step {item.sequence}",
                    'role': item.role,
                    'user_id': item.user_id.id if item.user_id else False,
                })
            doc.template_id = template

    # ==================== Internal Logic ====================

    def _activate_next_step(self):
        """Activate the next draft step (lowest sequence)"""
        self.ensure_one()
        next_item = self.request_item_ids.filtered(
            lambda i: i.state == 'draft'
        ).sorted('sequence')[:1]
        if next_item:
            next_item.write({
                'state': 'pending',
                'date_sent': fields.Datetime.now(),
            })
            next_item._send_notification_email()
        else:
            self._check_workflow_complete()

    def _check_workflow_complete(self):
        """Check if all steps are done → mark document as done"""
        self.ensure_one()
        if all(item.state == 'done' for item in self.request_item_ids):
            self.write({
                'state': 'done',
                'date_done': fields.Datetime.now(),
            })
    def action_view_attachments(self):
        attachment_ids = self.attachment_id.ids 
        action = self.env.ref('sign_dochub.ds_attachment_action').read()[0]
        action['domain'] = [('id', 'in', attachment_ids)]
        action['target'] = 'current'
        return action
    
    def action_view_sign_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lịch sử ký',
            'res_model': 'ds.sign.log',  # model lịch sử của bạn
            'view_mode': 'list',
        'domain': [('document_id', '=', self.id)],
        'target': 'current',
        }
    def action_open_sign_position(self):
        """Open the full-screen sign position editor (client action)"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'ds_sign_position_editor',
            'target': 'main',
            'context': {
                'document_id': self.id,
            },
            'name': 'Đặt vị trí ký',
        }
    def action_confirm_positions(self):
        """
        Button [Gửi quy trình]: Finish adjusting.

        Yêu cầu bắt buộc:
          1. Phải có ít nhất 1 request item.
          2. Tất cả request items phải đã đặt vị trí ký
             (signature_pos_x hoặc signature_pos_y khác 0).
             Nếu chưa → raise UserError hướng dẫn người dùng
             nhấn "Đặt vị trí ký" trước.
        """
        for doc in self:
            # --- Kiểm tra 1: phải có bước ký ---
            if not doc.request_item_ids:
                raise UserError(
                    "Vui lòng thêm ít nhất một bước ký trước khi gửi quy trình."
                )

            # --- Kiểm tra 2: tất cả bước phải đã đặt vị trí ký ---
            missing = doc.request_item_ids.filtered(
                lambda i: not (
                    i.role == 'approve'
                    or
                    (i.signature_pos_x or 0) != 0
                    or (i.signature_pos_y or 0) != 0
                )
            )
            if missing:
                signers = ', '.join(
                    item.user_id.name or f'Bước {item.sequence}'
                    for item in missing
                )
                raise UserError(
                    f"Bạn chưa đặt vị trí ký cho: {signers}.\n\n"
                    "Vui lòng nhấn nút «Đặt vị trí ký» để xác định vị trí "
                    "chữ ký trên tài liệu trước khi gửi quy trình."
                )

            # --- Tất cả hợp lệ → tiếp tục ---
            doc.write({'position_confirmed': True})
            has_started = any(item.state != 'draft' for item in doc.request_item_ids)
            if not has_started:
                doc._activate_next_step()
