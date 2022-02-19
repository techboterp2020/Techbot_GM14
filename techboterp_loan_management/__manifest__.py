# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

{
    'name': 'Loan Management',
    'summary': """Employee Loan Management""",
    'description': """
       index.html
    """,
    'author': 'Techbot ERP',
    'website': 'https://techboterp.com/',
    'category': 'Generic Modules/Human Resources',
    'version': '14.0.1.4',
    'license': 'OPL-1',
    'depends': ['hr_payroll', 'account_accountant', 'hr_payroll_account'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/hr_payroll_data.xml',
        'data/hr_payslip_data.xml',
        'data/emp_loan_data.xml',
        'data/cron.xml',
        'views/hr_loan_view.xml',
        'views/emp_loan_procedure_view.xml',
    ],
    'demo': [],
    'images': ['static/description/techbot_loan_management.jpg'],
    "price": 80,
    "currency": "EUR",
    'installable': True,
    'application': True,
    'auto_install': False,
}
