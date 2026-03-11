import base64
import io
import uuid

from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
from markupsafe import Markup

_logger = logging.getLogger(__name__)

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

    def _burn_signature_to_pdf(self, document):
        """Burns the signature text onto the PDF and updates signed_attachment_id."""
        try:
            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas
            from reportlab.lib.colors import blue
        except ImportError:
            raise UserError("Thiếu thư viện PyPDF2 hoặc reportlab. Không thể ký PDF.")

        if not document.attachment_id:
            return

        # Lấy file PDF nguồn (file đã ký nếu có, hoặc file gốc)
        source_attachment = document.signed_attachment_id or document.attachment_id[0]
        pdf_content = base64.b64decode(source_attachment.datas)
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        pdf_writer = PdfWriter()

        page_num = self.page_number - 1 if self.page_number > 0 else 0
        if page_num >= len(pdf_reader.pages):
            page_num = len(pdf_reader.pages) - 1

        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            
            if i == page_num:
                # Tạo watermark chữ ký bằng ReportLab
                packet = io.BytesIO()
                # Kích thước trang PDF (points)
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                
                can = canvas.Canvas(packet, pagesize=(width, height))
                can.setFillColor(blue)
                can.setFont("Helvetica-Bold", 16)
                
                # Tọa độ từ UI màn hình (thường là top-left) cần chuyển đổi sang (bottom-left) của PDF
                # UI scale thường khác với PDF points, nhưng tạm dùng trực tiếp or fixed tỉ lệ
                # Lấy tên đã ký từ note (được set từ UI javascript)
                signer_name = self.user_id.name or self.name or "Signed"
                if self.note and self.note.startswith("Đã ký bằng tên: "):
                    signer_name = self.note.replace("Đã ký bằng tên: ", "").strip()
                
                # Reportlab gốc toạ độ (0,0) ở góc dưới bên trái. UI toạ độ (0,0) ở góc trên bên trái.
                # height * 1.5 - y (do scale 1.5 trên JS)
                # Tạm thời convert X, Y thô
                pdf_x = self.signature_pos_x / 1.5  # JS scale is 1.5
                pdf_y = height - (self.signature_pos_y / 1.5) - 20 # -20 to adjust text baseline

                can.drawString(pdf_x, pdf_y, signer_name)
                can.setFont("Helvetica", 10)
                can.drawString(pdf_x, pdf_y - 12, "Signed on: " + fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                can.save()

                packet.seek(0)
                watermark_pdf = PdfReader(packet)
                watermark_page = watermark_pdf.pages[0]
                
                page.merge_page(watermark_page)
                
            pdf_writer.add_page(page)

        # Lưu file PDF mới
        output = io.BytesIO()
        pdf_writer.write(output)
        output_data = base64.b64encode(output.getvalue())

        # Tạo hoặc cập nhật attachment đã ký
        if document.signed_attachment_id:
            document.signed_attachment_id.write({'datas': output_data})
        else:
            new_attachment = self.env['ir.attachment'].create({
                'name': f"{document.name}_signed.pdf",
                'type': 'binary',
                'datas': output_data,
                'res_model': 'ds.document',
                'res_id': document.id,
                'mimetype': 'application/pdf'
            })
            document.write({'signed_attachment_id': new_attachment.id})

    def action_approve(self):
        """Approve/Sign this step"""
        for item in self:
            item.write({
                'state': 'done',
                'date_action': fields.Datetime.now(),
            })
            if item.signature_pos_x or item.signature_pos_y:
                item._burn_signature_to_pdf(item.document_id)
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
                body=Markup(f"Step '{item.name}' rejected by {item.user_id.name}. Note: {item.note or ''}"),
                message_type='notification',
            )

    def _send_notification_email(self):
        """Send email notification to signer"""
        # Lấy email từ SMTP server đã cấu hình (để tránh bị Gmail reject)
        smtp_server = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        smtp_email_from = smtp_server.smtp_user if smtp_server and smtp_server.smtp_user else None

        for item in self:
            # Xác định email nhận
            email_to = None
            if item.email:
                email_to = item.email
            elif item.user_id and item.user_id.email:
                email_to = item.user_id.email
            elif item.partner_id and item.partner_id.email:
                email_to = item.partner_id.email

            if not email_to:
                continue

            doc = item.document_id
            company = doc.company_id or self.env.company

            # email_from luôn dùng SMTP account để Gmail không reject
            email_from = smtp_email_from or company.email or self.env.user.email or 'noreply@example.com'

            # Build portal URL
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            portal_url = f"{base_url}/web#id={doc.id}&model=ds.document&view_type=form"

            role_label = dict(item._fields['role'].selection).get(item.role, '')
            create_date_str = doc.create_date.strftime('%Y-%m-%d %H:%M:%S') if doc.create_date else ''

            table_rows = f"""
                <tr>
                    <td style="padding:8px;border:1px solid #555;">1</td>
                    <td style="padding:8px;border:1px solid #555;">
                        <a href="{portal_url}" style="color:#4e9af1;">{doc.name}</a>
                    </td>
                    <td style="padding:8px;border:1px solid #555;">{role_label}</td>
                    <td style="padding:8px;border:1px solid #555;">{doc.creator_id.name or ''}</td>
                    <td style="padding:8px;border:1px solid #555;">{create_date_str}</td>
                    <td style="padding:8px;border:1px solid #555;">{doc.name}</td>
                </tr>
            """

            recipient_name = (
                item.user_id.name
                or (item.partner_id.name if item.partner_id else None)
                or email_to
            )

            body_html = f"""
            <div style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
                <div style="background-color:#2d5fa6;padding:20px;text-align:center;">
                    <h2 style="color:white;margin:0;">{company.name}</h2>
                </div>
                <div style="background-color:#1a1a2e;color:#e0e0e0;padding:24px;">
                    <p>Kính chào {recipient_name},</p>
                    <p>Chứng từ <strong>{doc.name}</strong> đang chờ, vui lòng nhấn vào chứng từ hoặc sử dụng Mã xử lý ở bên dưới để xử lý chứng từ.</p>
                    <table style="width:100%;border-collapse:collapse;margin:16px 0;color:#e0e0e0;">
                        <thead>
                            <tr style="background-color:#333;">
                                <th style="padding:8px;border:1px solid #555;text-align:left;">STT</th>
                                <th style="padding:8px;border:1px solid #555;text-align:left;">Mã chứng từ</th>
                                <th style="padding:8px;border:1px solid #555;text-align:left;">Quyền xử lý</th>
                                <th style="padding:8px;border:1px solid #555;text-align:left;">Người tạo</th>
                                <th style="padding:8px;border:1px solid #555;text-align:left;">Ngày tạo</th>
                                <th style="padding:8px;border:1px solid #555;text-align:left;">Mã xử lý</th>
                            </tr>
                        </thead>
                        <tbody>
                            {table_rows}
                        </tbody>
                    </table>
                    <p>Hạn xử lý bằng link và mã xử lý:</p>
                    <p>Vui lòng truy cập vào hệ thống để xử lý chứng từ.</p>
                    <p><strong>Xin chân thành cảm ơn.</strong></p>
                </div>
                <div style="background-color:#f5f5f5;color:#888;padding:12px;text-align:center;font-size:12px;">
                    <p>Đây là email tự động, vui lòng không trả lời lại thư này.</p>
                    <p>Xin cảm ơn</p>
                    <br/>
                    <p><strong>Powered by</strong></p>
                    <p>{company.street or ''}, {company.city or ''}</p>
                    <p>{company.name} version 1.0</p>
                </div>
            </div>
            """

            mail_values = {
                'subject': f"Chứng từ {doc.name} đang chờ {role_label}",
                'email_to': email_to,
                'email_from': email_from,
                'reply_to': email_from,
                'body_html': body_html,
                'auto_delete': True,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()

            # Log vào chatter
            item.document_id.message_post(
                body=Markup(f"📧 Đã gửi email yêu cầu <b>{role_label}</b> tới <b>{email_to}</b> cho bước <b>{item.name or role_label}</b>."),
                message_type='notification',
            )
        