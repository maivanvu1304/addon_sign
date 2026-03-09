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
    ],
    'application': True,
    "installable": True,
    'license': 'LGPL-3',
}
