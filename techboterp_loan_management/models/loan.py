import time
import math

from lxml import etree
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrLoanManagement(models.Model):
    _name = 'hr.loan.management'
    _description = "Employee Loan Management"
    _inherit = ['mail.thread']

    @api.depends('date_start', 'time_duration_month')
    def date_due_calculation(self):
        for record in self:
            record.date_due = False
            if record.date_start:
                record.date_due = record.date_start + timedelta(record.time_duration_month * 365 / 12)

    @api.depends('loan_amt', 'installment_lines', 'installment_lines.amt')
    def amount_calculate(self):
        for record in self:
            amount_paid = 0.0
            for installment in record.installment_lines:
                amount_paid += installment.amt
            record.paid_amt = amount_paid
            record.amount_to_pay = record.loan_amt - amount_paid

    name = fields.Char('Loan Number', size=64, required=True, default=_('New'))

    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, store=True,
                                  default=lambda self: self.env.user.employee_id)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('waiting', 'Waiting'),
                              ('refuse', 'Refused'),
                              ('approve', 'Approved'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], string="Status", required=True, default='draft', tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
                                    store=True)
    loan_type = fields.Selection([('payroll', 'Loan Against Payroll'), ('service', 'Loan Against Service')],
                                 string="Loan Type", required=True, default='payroll')
    loan_applied_date = fields.Date('Loan Applied Date', required=True, default=fields.Date.today)
    date_start = fields.Date('Loan Payment From Date', tracking=True)
    date_due = fields.Date('Loan Payment Due Date', tracking=True, compute='date_due_calculation', store=True)
    loan_amt = fields.Float('Loan Amount', digits='Account', required=True, tracking=True)
    amt_deduction = fields.Float('Deduction Amount', digits='Account', copy=False)
    time_duration_month = fields.Integer('Payment Time Duration', tracking=True, copy=False)
    emi_based_on = fields.Selection([('month', 'By Month'), ('amount', 'By Amount')], string='EMI based on',
                                    required=True, default='month', tracking=True)
    paid_amt = fields.Float('Paid Amount', compute='amount_calculate', digits='Account',
                            tracking=True)
    amount_to_pay = fields.Float('Amount to Pay', compute='amount_calculate', digits='Account',
                                 tracking=True)
    installment_lines = fields.One2many('employee.installment.line', 'loan_id', string="Loan", )
    loan_lines = fields.One2many('employee.loan.line', 'loan_id', string="Loan Lines", index=True)
    description = fields.Text('Purpose For Loan', required=True)
    account_id = fields.Many2one('account.account', string="Account")
    account_emp_id = fields.Many2one('account.account', string="Employee Loan Account")
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')],
                                                                                         limit=1))
    loan_operation_ids = fields.Many2many('loan.procedure', compute='get_loan_procedure')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True,
                                          tracking=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags', tracking=True)
    account_move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    skip_installment_count = fields.Integer(compute='calculate_skip_installments')
    increase_amount_count = fields.Integer(compute='calculate_increase_loan_amount')
    pay_loan_count = fields.Integer(compute='pay_loan_amount_details')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.user.company_id)

    def get_loan_procedure(self):
        self.loan_operation_ids = self.env['loan.procedure'].search([('employee_id', '=', self.employee_id.id)])

    @api.depends('loan_operation_ids')
    def calculate_skip_installments(self):
        if self.loan_operation_ids:
            loan_operation_ids = self.mapped('loan_operation_ids').filtered(
                lambda operation: operation.loan_procedure_type == 'skip_installment')
            self.skip_installment_count = len(loan_operation_ids)

    @api.depends('loan_operation_ids')
    def calculate_increase_loan_amount(self):
        if self.loan_operation_ids:
            loan_operation_ids = self.mapped('loan_operation_ids').filtered(
                lambda operation: operation.loan_procedure_type == 'increase_amount')
            self.increase_amount_count = len(loan_operation_ids)

    @api.depends('loan_operation_ids')
    def pay_loan_amount_details(self):
        if self.loan_operation_ids:
            loan_operation_ids = self.mapped('loan_operation_ids').filtered(
                lambda operation: operation.loan_procedure_type == 'loan_payment')
            self.pay_loan_count = len(loan_operation_ids)

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id = False
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.company_id = self.employee_id.company_id.id
            contract = self.env['hr.contract'].search(
                [('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
            self.analytic_account_id = (contract and contract.analytic_account_id.id) or False
            # self.analytic_tag_ids = (contract and [(6, 0, contract.analytic_tag_ids.ids)]) or False

    @api.model
    def create(self, values):
        if values.get('employee_id'):
            loan_management_ids = self.env['hr.loan.management'].search([('state', 'not in', ['done', 'cancel']),
                                                                         ('employee_id', '=', values['employee_id'])])
            if loan_management_ids:
                raise UserError(_('loan is already in Process of this employee'))
        if values.get('company_id'):
            values['name'] = self.env['ir.sequence'].with_context(company=values['company_id']).next_by_code(
                'hr_loan_management') or _('New')
        else:
            values['name'] = self.env['ir.sequence'].next_by_code('hr_loan_management') or _('New')
        return super(HrLoanManagement, self).create(values)

    def write(self, values):
        if values.get('employee_id'):
            loan_management_ids = self.env['hr.loan.management'].search([('state', 'not in', ['done', 'cancel']),
                                                                         ('employee_id', '=', values['employee_id'])])
            if loan_management_ids:
                raise UserError(_('loan is already in Process of this employee'))
        return super(HrLoanManagement, self).write(values)

    def calculation_done(self):
        if not self.loan_amt or self.loan_amt < 0:
            raise UserError(_("Please enter proper value for Loan Amount & Interest"))
        if self.emi_based_on == 'month':
            if not self.time_duration_month or self.time_duration_month < 0:
                raise UserError(_("Please enter proper value for Payment Duration"))
            self.amt_deduction = self.loan_amt / self.time_duration_month
        elif self.emi_based_on == 'amount':
            if not self.amt_deduction or self.amt_deduction < 0:
                raise UserError(_("Please enter proper value of Deduction Amount"))
            self.time_duration_month = self.loan_amt / self.amt_deduction
        self.calculate_installment()

    def confirm(self):
        self.ensure_one()
        self.calculation_done()
        self.state = 'confirm'

    def waiting(self):
        self.ensure_one()
        self.state = 'waiting'

    def approve(self):
        self.ensure_one()
        timenow = time.strftime('%Y-%m-%d')
        for record in self:
            amount = record.loan_amt
            loan_name = record.employee_id.name
            reference = record.name
            journal_id = record.journal_id.id
            debit_account_id = record.account_id.id
            credit_account_id = record.account_emp_id.id
            analytic_account_id = record.analytic_account_id.id
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'analytic_account_id': analytic_account_id or False,
                'analytic_tag_ids': [(6, 0, record.analytic_tag_ids.ids)] or False,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'analytic_account_id': analytic_account_id or False,
                'analytic_tag_ids': [(6, 0, record.analytic_tag_ids.ids)] or False,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            }
            vals = {
                'name': reference,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
            record.account_move_id = move
        self.state = 'approve'

    def done(self):
        self.ensure_one()
        self.state = 'done'

    def refuse_loan(self):
        self.ensure_one()
        if self.installment_lines:
            raise UserError(_('loan having any installment can not be refused!'))
        self.state = 'refuse'

    def draft(self):
        self.ensure_one()
        self.state = 'draft'

    def cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def action_view_procedure_req(self):
        self.ensure_one()
        loan_operation_ids = self.loan_operation_ids.search([('employee_id', '=', self.employee_id.id),('loan_id', '=', self.id)])
        tree_view = self.env.ref('techboterp_loan_management.view_hr_loan_procedure_tree')
        form_view = self.env.ref('techboterp_loan_management.view_loan_procedure_form')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Loan Procedure Request'),
            'res_model': 'loan.procedure',
            'view_mode': 'from',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', 'in', loan_operation_ids.ids)],
            'context': {'group_by': 'loan_procedure_type', 'default_employee_id': self.employee_id.id,
                        'default_loan_id': self.id, 'default_analytic_account_id': self.analytic_account_id.id,
                        },
        }

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise UserError(_('You cannot delete a loan which is in %s state.') % rec.state)
            return super(HrLoanManagement, self).unlink()

    def calculate_installment(self):
        context = dict(self._context) or {}
        for record in self:
            if context.get('calculate_button'):
                record.loan_lines.unlink()
            else:
                record.loan_lines = [(5,)]
            start_date = datetime.strptime(str(record.date_start), '%Y-%m-%d')
            duration = 1.0
            amount = 1.0
            if record.emi_based_on == 'month':
                duration = record.time_duration_month
                amount = record.loan_amt / duration
            elif record.emi_based_on == 'amount':
                amount = record.amt_deduction
                duration = math.ceil(record.loan_amt / record.amt_deduction)

            for l_id in range(1, duration + 1):
                vals = {
                    'payment_date': start_date,
                    'amt': amount,
                    'employee_id': record.employee_id.id,
                    'loan_id': record.id
                }
                if record.emi_based_on == 'amount' and duration == l_id:
                    vals.update({'amt': abs(((duration - 1) * record.amt_deduction) - record.loan_amt)})
                self.env['employee.loan.line'].create(vals)
                start_date = start_date + relativedelta(months=1)


class HrEmployeeLoanLine(models.Model):
    _name = "employee.loan.line"
    _description = "Pre-Installment Line"

    # Created Date
    # date=fields.Date()
    payment_date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amt = fields.Float(string="Amount", required=True)
    loan_id = fields.Many2one('hr.loan.management', string="Loan Ref.")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
    operation_id = fields.Many2one('loan.procedure', string="Operation")
    state = fields.Selection([('draft', 'Pending'), ('skipped', 'Skipped'), ('paid', 'Paid'), ('cancel', 'Cancel')],
                             string="Status", default="draft")


class InstallmentLine(models.Model):
    _name = 'employee.installment.line'
    _description = 'Installment Line'

    loan_id = fields.Many2one('hr.loan.management', 'Loan', required=True)
    payslip_id = fields.Many2one('hr.payslip', 'Payslip', required=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    date = fields.Date('Date', required=True)
    amt = fields.Float('Installment Amount', digits='Account', required=True)
    operation_id = fields.Many2one('loan.procedure', 'Operation', required=False)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    loan_ids = fields.One2many('hr.loan.management', 'employee_id', 'Loans')
