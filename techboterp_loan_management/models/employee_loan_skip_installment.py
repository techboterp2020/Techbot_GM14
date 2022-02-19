# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, UserError
from dateutil import relativedelta

class EmployeeSkipInstallment(models.Model):
    _name = 'employee.skip.installment'
    _inherit = ['mail.thread']
    _description = "Loan Skip Installment of Employee"

    name = fields.Char('Reason to Skip',required=True, tracking=True)
    loan_id = fields.Many2one('hr.loan.management','Loan',domain="[('employee_id','=',employee_id), ('state','=', 'approve')]",required=True, tracking=True)
    employee_id = fields.Many2one('hr.employee','Employee',required=True, default=lambda self: self.env['hr.employee'].get_employee(), tracking=True)
    today_date = fields.Date('Date', required=True, default=fields.Date.today, tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('waiting', 'Waiting'),
                              ('refuse', 'Refused'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled')], string="Status",required=True, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False, default=lambda self: self.env.user.company_id)


    @api.constrains('today_date', 'employee_id', 'loan_id', 'company_id')
    def check_today_date(self):
        employee_ids = self.search([('id', '!=', self.id), ('employee_id', '=', self.employee_id.id), ('loan_id', '=', self.loan_id.id), ('company_id','=',self.company_id.id)])
        current_month = datetime.now().month
        for employee_id in employee_ids:
            date_skip = datetime.strptime(str(employee_id.date), DEFAULT_SERVER_DATE_FORMAT)
            if int(current_month) == int(date_skip.month):
                raise ValidationError(_('For thid month record is already available in system!'))

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            self.company_id = self.employee_id.company_id.id

    def confirm(self):
        self.ensure_one()
        loan_procedure_ids = self.env['loan.procedure'].search([('loan_id', '=', self.loan_id.id), ('state', 'not in', ['refuse', 'done']), ('loan_operation_type', '=', 'pay_loan_amount')])

        if any(self.date.month == loan_procedure.date.month and loan_procedure.loan_procedure_type == 'pay_loan_amount' for loan_procedure in loan_procedure_ids):
            raise UserError(_('Please Cancel Your  loan Request'))
        self.state = 'confirm'

    def waiting(self):
        self.ensure_one()
        self.state = 'waiting'

    def approve(self):
        self.ensure_one()
        if self.loan_id.state == 'approve':
            end_date = self.loan_id.date_due + relativedelta(months=+1)
            self.loan_id.write({'date_due': end_date})
            self.state = 'approve'
        else:
            raise ValidationError(_('You pending loan to approve'))

    def refuse(self):
        self.ensure_one()
        if self.state == 'confirm':
            due_date = datetime.strptime(str(self.loan_id.date_due), DEFAULT_SERVER_DATE_FORMAT)
            end_date = due_date + relativedelta(months=-1)
            self.loan_id.write({'date_due': end_date})
        self.state = 'refuse'

    def draft(self):
        self.ensure_one()
        self.state = 'draft'

    def cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'cancel']:
                raise ValidationError(_('You cannot delete a request to skip installment which is in %s state.')%(record.state))
        return super(EmployeeSkipInstallment, self).unlink()
