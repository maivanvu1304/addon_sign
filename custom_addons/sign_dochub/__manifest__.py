{
    'name': 'sign_dochub',
    'description': """
Long description of module's purpose
    """,
    'version': '19.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Sequential document signing workflow with multi-step sign/approve',
    'depends': ['base', 'hr', 'mail', 'portal'],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        # Views
        'views/ds_document_views.xml',
        'views/ds_document_type_views.xml',
        'views/ds_document_template_views.xml',
        'views/ds_document_menus.xml',
        'views/ds_attachment_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'sign_dochub/static/src/js/sign_position_editor.js',
            'sign_dochub/static/src/xml/sign_position_editor.xml',
            'sign_dochub/static/src/scss/sign_position_editor.scss',
            'sign_dochub/static/src/js/ds_pdf_preview.js',
            'sign_dochub/static/src/xml/ds_pdf_preview.xml',
            'sign_dochub/static/src/scss/ds_pdf_preview.scss',
            'sign_dochub/static/src/js/sign_document.js',
            'sign_dochub/static/src/xml/sign_document.xml',
        ],
    },
    'application': True,
    "installable": True,
    'license': 'LGPL-3',
}
