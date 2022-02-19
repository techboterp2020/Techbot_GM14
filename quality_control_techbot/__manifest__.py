
{
    'name': 'Quality Control',
    'version': '14.0.1.0.0',
    'category': 'Quality Control',
    'summary': "Quality Control For the product at the time of Purchase ",
    'author': 'Techbot ERP',
    'company': 'Technoat ERP',
    'website': 'https://techboterp.com/',
    'description': """  """,
    'depends': ['purchase','stock'],
    'data': [
        'data/qc_data.xml',
        'security/ir.models.access.csv',
        'report/qc_action.xml',
        'report/qc_outgoing_receipt_report.xml',
        'views/stock_picking_view.xml',
        'views/quality_conrol_view.xml'
    ],
    'images': ['static/description/techbot_quality_control.jpg'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
    "price": 70,
    "currency": "EUR"
}
