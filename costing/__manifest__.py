{
    'name': 'Estimation',
    'version': '1.0',
    'author': 'Anup',
    'category': 'Production',
    'website': '',
    'description': """
        Capable of Estimating
         """,

    'summary': 'Estimation',
    'depends': ['base_setup', 'base', 'stock', 'hr', 'contacts', 'mail', 'crm', 'sale'],
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
