{
    'name': 'Costing and Estimation',
    'version': '14.0.0.1',
    'description': """
        Module for Capable of Estimating and Costing in Production Version 14
         """,
    'category': 'Production',
    'author': 'TecbotERp',
    'website': "https://techboterp.com",
    'company': 'TechbotErp',
    'license': 'LGPL-3',
    'complexity': 'easy',
    'images': [],
    'sequence': -10,
    'summary': 'Product Estimation',
    'depends': ['base',
                'stock',
                'hr',
                'contacts',
                'mail',
                'crm',
                'sale',
                'mrp'
                ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/report_template.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/report_email_template.xml',
        'report/estimate_report.xml',
        'view/costing_view.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}
