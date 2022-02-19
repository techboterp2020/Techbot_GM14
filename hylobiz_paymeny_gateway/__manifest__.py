{
    'name': 'UAE Payment Gateway (Hylobiz)',
    'version': '1.0',
    'author': 'TechBot ERP',
    'category': 'account',
    'website': 'https://www.techboterp.com/',
    'description': """
        AED Payment Gateway Integration
         """,

    'summary': 'AED Payment Gateway',
    'depends': ['web','base',  'account', 'sale'],
    'data': [
        'views/templates.xml',
        'views/hylo_view.xml',
        'data/payment_acquirer_data.xml',
    ],
    'images': ['static/description/hylobiz_payment_gateway.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    "price": 90,
    "currency": "EUR"
}
