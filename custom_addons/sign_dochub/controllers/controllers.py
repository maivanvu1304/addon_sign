# from odoo import http


# class SignDochub(http.Controller):
#     @http.route('/sign_dochub/sign_dochub', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sign_dochub/sign_dochub/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('sign_dochub.listing', {
#             'root': '/sign_dochub/sign_dochub',
#             'objects': http.request.env['sign_dochub.sign_dochub'].search([]),
#         })

#     @http.route('/sign_dochub/sign_dochub/objects/<model("sign_dochub.sign_dochub"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sign_dochub.object', {
#             'object': obj
#         })
