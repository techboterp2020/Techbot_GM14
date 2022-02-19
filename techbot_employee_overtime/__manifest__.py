# -*- coding: utf-8 -*-
{
    'name': 'UAE HR Employee Overtime',
    'summary': 'UAE HR Employee Overtime',
    'description': """
        Calculate employee overtime based on employee overtime.
    """,
    'author': 'Techbot ERP',
    'website': 'https://techboterp.com/',
    'category': 'HR',
    'version': '1.0',
    'license': 'OPL-1',
    'depends': ['hr', 'hr_contract', 'hr_payroll'],
    'data': [
        'security/ir.models.access.csv',
        'data/payroll_data.xml',
        'views/hr_contract_view.xml',
        'views/overtime_view.xml'
    ],
    'demo': [],
    "price": 20,
    "currency": "EUR",
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
}
