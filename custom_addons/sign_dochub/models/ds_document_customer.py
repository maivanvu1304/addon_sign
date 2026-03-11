import random
import string

from odoo import models, fields, api
from markupsafe import Markup


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
        """Send notification email to customer"""
        smtp_server = self.env['ir.mail_server'].sudo().search([], order='sequence asc', limit=1)
        smtp_email_from = smtp_server.smtp_user if smtp_server and smtp_server.smtp_user else None

        for customer in self:
            doc = customer.document_id
            if not customer.email:
                continue

            company = doc.company_id or self.env.company
            email_from = smtp_email_from or company.email or self.env.user.email or 'noreply@example.com'

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            portal_url = f"{base_url}/my/documents/{doc.id}?access_token={customer.verification_code}"

            create_date_str = doc.create_date.strftime('%d/%m/%Y %H:%M') if doc.create_date else ''
            doc_type_name = doc.document_type_id.name if doc.document_type_id else 'Giấy chứng nhận'
            title = doc.title or doc_type_name
            customer_code = customer.partner_id.ref or customer.partner_id.name

            body_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 800px; margin: auto; border: 1px solid #e0e0e0;">
                <div style="background-color: #4a7ee6; padding: 20px; text-align: center; color: white;">
                    <h2 style="margin: 0; font-size: 20px;">Trung tâm Kỹ thuật Tiêu chuẩn Đo lường Chất lượng 3</h2>
                    <p style="margin: 5px 0 0; font-size: 16px;">QUATEST 3</p>
                </div>
                <div style="padding: 24px; color: #333;">
                    <p><strong>Kính chào Quý khách hàng,</strong></p>
                    <p>Chúng tôi xin thông báo về chứng từ <strong>{title}</strong> đã được tạo trong hệ thống.</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px;">
                        <thead>
                            <tr style="background-color: #4a7ee6; color: white;">
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: left; width: 40%;">Thông tin</th>
                                <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Chi tiết</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Tên chứng từ</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{title}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Mã chứng từ</td>
                                <td style="padding: 10px; border: 1px solid #ddd; color: #4a7ee6;">{doc.name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Mã khách hàng</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{customer_code}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Ngày tạo</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{create_date_str}</td>
                            </tr>
                            <tr>
                                <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Số lượng tài liệu</td>
                                <td style="padding: 10px; border: 1px solid #ddd;">{len(doc.attachment_id)} tài liệu</td>
                            </tr>
                        </tbody>
                    </table>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{portal_url}" style="background-color: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 15px;">🔍 Xem Chi Tiết Chứng Từ</a>
                    </div>

                    <div style="background-color: #f1f3f4; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
                        <p style="margin: 0 0 10px 0; font-weight: bold; color: #555;">📋 Hướng dẫn:</p>
                        <ul style="margin: 0; padding-left: 20px; color: #555; font-size: 13px;">
                            <li style="margin-bottom: 5px;">Nhấn vào nút "Xem Chi Tiết Chứng Từ" để truy cập thông tin đầy đủ</li>
                            <li style="margin-bottom: 5px;">Sử dụng mã khách hàng <strong style="color: #28a745;">{customer_code}</strong> khi liên hệ với chúng tôi</li>
                            <li>Mọi thắc mắc xin liên hệ hotline: <strong>028 382 942 74 | 028 382 930 12</strong></li>
                        </ul>
                    </div>

                    <p style="margin-bottom: 5px;">Cảm ơn Quý khách đã tin tưởng sử dụng dịch vụ của QUATEST 3.</p>
                    <p style="margin-top: 20px; font-weight: bold;">Trân trọng,<br/>Đội ngũ QUATEST 3</p>
                </div>
            </div>
            """

            attachment_ids = []
            if doc.signed_attachment_id:
                attachment_ids.append(doc.signed_attachment_id.id)
            elif doc.attachment_id:
                attachment_ids.extend(doc.attachment_id.ids)

            mail_values = {
                'subject': f"QUATEST 3 - Thông báo chứng từ {title}",
                'email_to': customer.email,
                'email_from': email_from,
                'reply_to': email_from,
                'body_html': body_html,
                'attachment_ids': [(6, 0, attachment_ids)],
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()

            customer.write({
                'is_sent': True,
                'date_sent': fields.Datetime.now(),
            })

            doc.message_post(
                body=Markup(f"📧 Đã gửi email ban hành kết quả cho khách hàng <b>{customer.partner_id.name}</b> ({customer.email})."),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    def action_preview(self):
        """Preview document as customer would see it (placeholder)"""
        pass
