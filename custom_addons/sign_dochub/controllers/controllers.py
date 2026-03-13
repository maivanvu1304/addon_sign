from odoo import http
from odoo.http import request
from odoo.tools import str2bool
from werkzeug.exceptions import NotFound

class DsDocumentPortal(http.Controller):
    
    @http.route(['/my/documents/<int:document_id>'], type='http', auth='public', website=True)
    def portal_my_document(self, document_id, access_token=None, **kw):
        # Fetch the document customer record using access_token
        customer_record = request.env['ds.document.customer'].sudo().search([
            ('document_id', '=', document_id),
            ('verification_code', '=', access_token)
        ], limit=1)

        if not customer_record:
            return request.render('website.404')

        document = customer_record.document_id

        # Make sure document has an access token if we are going to use it for attachment download
        if hasattr(document, 'access_token') and not document.access_token:
            document._compute_access_url() # This usually generates it for portal mixins, but let's just use the sudo document directly.
            
        # Instead of generic /web/content/, we should pass a tokenized URL or just render inline since we sudoed.
        # But Odoo's /web/content/ requires login. So we will create a custom route to download the PDF without login if token is valid.

        values = {
            'document': document,
            'customer': customer_record,
            'page_name': 'document_portal',
            'token': access_token,
        }
        
        return request.render('sign_dochub.ds_document_portal_template', values)

    @http.route(['/my/documents/<int:document_id>/download'], type='http', auth='public')
    def portal_download_document(self, document_id, access_token=None, download=False, **kw):
        customer_record = request.env['ds.document.customer'].sudo().search([
            ('document_id', '=', document_id),
            ('verification_code', '=', access_token)
        ], limit=1)

        if not customer_record:
            raise NotFound()

        document = customer_record.document_id

        attachment = document.signed_attachment_id or (document.attachment_id and document.attachment_id[0]) or None
        
        if not attachment:
            raise NotFound()

        stream = request.env['ir.binary'].sudo()._get_stream_from(
            attachment.sudo(),
            'raw',
            filename=attachment.name,
            filename_field='name',
            mimetype=attachment.mimetype,
        )
        stream.public = True
        return stream.get_response(as_attachment=str2bool(download))
