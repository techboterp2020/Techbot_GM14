# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time

class HrLoanProcedure(models.Model):
    _name = 'loan.procedure'
    _inherit = ['mail.thread']
    _description = 'Loan Procedure'


    def get_employee_details(self):
        recode = self.env['hr.loan.management'].search([('state', '=', 'approve')])
        employee_id = []
        for loan in recode:
            employee_id.append(loan.employee_id)
        return employee_id

    name = fields.Char('Name', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    loan_procedure_type = fields.Selection([('skip_installment', 'Installment Skip'),
                                            ('increase_amount', 'Loan Amount Increase'),
                                            ('loan_payment', 'Payment Details')], required=True, default='skip_installment')
    skip_reason = fields.Char('Reason of Skip', tracking=True)
    loan_id = fields.Many2one('hr.loan.management', 'Loan',
                              domain="[('employee_id','=',employee_id), ('state','=', 'approve')]", required=True,
                              tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                  default=lambda self: self.env['hr.employee'], tracking=True)
    # loan_id = fields.Many2one('hr.loan.management', 'Loan', required=True, tracking=True ,domain="[('employee_id','=',employee_id), ('state','=', 'approve')]")
    # employee_id = fields.Many2one('hr.employee', 'Employee', required=True, tracking=True, domain=lambda self: self.get_employee_details())
    # employee_id = fields.Many2one('hr.employee', 'Employee', required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id', store=True)
    date_effective = fields.Date('Date of Effective', default=fields.Date.today, tracking=True)
    # Ajmal added new fields
    effective_date = fields.Date('Date  Effective', default=fields.Date.today, tracking=True)
    resent_loan_amount = fields.Float('Resent Loan Amount',  readonly=True)
    amt_to_pay = fields.Float('Amount to Pay', readonly=True)
    loan_amt = fields.Float('Increase Loan Amount', copy=False)
    payment_details = fields.Selection([('fully', 'Fully'), ('partially', 'Partially')], default='fully', copy=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.user.company_id)
    payment_amt = fields.Float('Payment Amount')
    payment_type = fields.Selection([('by_payslip', 'By Payslip'), ('by_account', 'By Account')], default='by_payslip')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('waiting', 'Waiting'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('refuse', 'Refused'),
                              ('done', 'Done')],
                             default='draft', copy=False)
    account_id = fields.Many2one('account.account', string="Account")
    employee_account_id = fields.Many2one('account.account', string="Employee Loan Account")
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 default=lambda self: self.env['account.journal'].search([('type', '=', 'general')], limit=1))

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
    account_move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    accounting_info = fields.Boolean('Accounting Info', default=False, compute='compute_accounting_info')
    procedure_applied = fields.Boolean('Effect Applied on Loan?', default=False)
    next_schedule_id = fields.Many2one('employee.loan.line', string="Loan Schedule", copy=False)

    # def get_employee_details(self):
    #     domain = []
    #     loan_obj = self.env['hr.loan.management']
    #     employee_id = loan_obj.search([('state', '=', 'approve')]).mapped('employee_id')
    #     domain.append(('id', 'in', employee_id.ids))
    #     return domain

    # @api.onchange('loan_id')
    # def onchange_loan(self):
    #     for record in self:
            # record.analytic_account_id = (record.loan_id and record.loan_id.analytic_account_id.id) or False
            # # record.analytic_tag_ids = (record.loan_id and [(6, 0, record.loan_id.analytic_tag_ids.ids)]) or False
            # record.account_id = (record.loan_id and record.loan_id.account_id.id) or False
            # record.empolyee_account_id = (record.loan_id and record.loan_id.account_emp_id.id) or False

    @api.depends('loan_procedure_type', 'state', 'payment_type')
    def compute_accounting_info(self):
        for record in self:
            if record.state in ['waiting', 'approve'] and record.loan_procedure_type == 'increase_amount':
                record.accounting_info = True
            elif record.state in ['waiting', 'approve'] and record.loan_procedure_type == 'loan_payment' and record.payment_type == 'by_account':
                record.accounting_info = True
            else:
                record.accounting_info = False

    def check_loan_details_procedure(self, employee, date_effective, type):
        loan_procedure_ids = self.search([('state', 'in', ['confirm', 'waiting', 'approve']), ('employee_id', '=', employee.id), ('id', '!=', self.id)])
        for record in loan_procedure_ids:
            if record.loan_procedure_type == 'increase_amount' and type != 'increase_amount' and record.effective_date.month == date_effective.month and record.effective_date.year == date_effective.year:
                raise ValidationError(_('In this month %s has already request for incrase amount Please check loan operation request!!' % employee.name))
            elif record.loan_procedure_type == 'skip_installment' and record.effective_date.month == date_effective.month and record.effective_date.year == date_effective.year:
                raise ValidationError(_('In this month %s has already request for skip installment Please check loan operation request!!' % employee.name))
            elif record.loan_procedure_type == 'loan_payment' and record.effective_date.month == date_effective.month and record.effective_date.year == date_effective.year:
                raise ValidationError(_('In this month %s has already request for loan payment Please check loan operation request!!' % employee.name))

    @api.constrains('loan_amt', 'payment_amt')
    def check_loan_amount(self):
        for record in self:
            if record.payment_details == 'increase_amount' and record.loan_amt <= 0:
                raise ValidationError(_('Loan Amount Must be Greater than 0!!'))
            elif record.loan_procedure_type == 'loan_payment' and record.payment_details == 'partially' and record.payment_amt <= 0:
                raise ValidationError(_('Loan Amount Pay Must be Greater than 0!!'))

    @api.onchange('payment_details')
    def onchange_payment_details(self):
        if self.payment_details:
            self.payment_amt = False

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            loan_id = self.env['hr.loan.management'].search([('state', '=', 'approve'), ('employee_id', '=', self.employee_id.id)])
            if not loan_id:
                raise UserError(_('%s has not any running loan request.' % self.employee_id.name))

    @api.onchange('loan_procedure_type')
    def onchange_loan_procedure_type(self):
        if self.loan_procedure_type:
            self.skip_reason = False
            self.loan_amt = False
            self.payment_details = 'fully'

    @api.model
    def create(self, values):
        if values.get('name', _('New')) == _('New'):
            seq_date = None
            if 'company_id' in values:
                values['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                    'loan.procedure') or _('New')
            else:
                values['name'] = self.env['ir.sequence'].next_by_code('loan.procedure') or _('New')
        res = super(HrLoanProcedure, self).create(values)
        if res.employee_id and res.loan_id and res.date_effective:
            if res.loan_procedure_type == 'loan_payment' and res.payment_details == 'partially':
                if res.payment_amt >= res.loan_id.amt_to_pay:
                    raise UserError(_('Amount should be less then  amount to pay!'))
        return res

    def write(self, values):
        for record in self:
            if values.get('loan_procedure_type') == 'loan_payment' or values.get('payment_details') == 'partially' or values.get('payment_amt'):
                if values.get('payment_amount') and values.get('payment_amount') > record.loan_id.amount_to_pay:
                    raise UserError(_('Amount should be less then amount to pay!'))
        return super(HrLoanProcedure, self).write(values)

    def draft(self):
        self.ensure_one()
        self.state = 'draft'
        self.journal_id = False
        self.account_id = False
        self.employee_account_id = False
        self.analytic_account_id = False
        self.procedure_applied = False


    def confirm(self):
        self.ensure_one()
        self.check_loan_details_procedure(self.employee_id, self.date_effective, self.loan_procedure_type)
        self.state = 'confirm'

    def waiting(self):
        self.ensure_one()
        self.state = 'waiting'

    def approve(self):
        self.ensure_one()
        # self.approved_by = self.env['res.users'].id

        # self.approved_by = self.env.uid
        # self.approved_date = datetime.today()
        timenow = time.strftime('%Y-%m-%d')
        for record in self:
            if record.payment_type == 'by_account' or record.loan_procedure_type == 'increase_amount':
                amount = record.loan_amt
                if record.loan_procedure_type == 'loan_payment':
                    if record.payment_details == 'fully':
                        amount = record.loan_id.loan_amt
                        record.loan_id.state = 'done'
                    else:
                        amount = record.payment_amt
                loan_name = 'loan operation for %s' % record.employee_id.name
                reference = 'loan operation for %s' % record.employee_id.name
                journal_id = record.journal_id.id
                debit_account_id = record.account_id.id
                credit_account_id = record.employee_account_id.id

                debit_vals = {
                    'name': loan_name,
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'analytic_account_id': record.analytic_account_id.id or False,
                    'debit': amount > 0.0 and amount or 0.0,
                    'credit': amount < 0.0 and -amount or 0.0,
                    # 'loan_id': loan.id,
                    'analytic_tag_ids': [(6, 0, record.analytic_tag_ids)],
                }
                credit_vals = {
                    'name': loan_name,
                    'partner_id': record.employee_id.address_home_id.id,
                    'account_id': credit_account_id,
                    'analytic_account_id': record.analytic_account_id.id or False,
                    'journal_id': journal_id,
                    'date': timenow,
                    'debit': amount < 0.0 and -amount or 0.0,
                    'credit': amount > 0.0 and amount or 0.0,
                    # 'loan_id': loan.id,
                    'analytic_tag_ids': [(6, 0, record.analytic_tag_ids)],
                }
                vals = {
                    'name': 'Loan For' + ' ' + loan_name,
                    'narration': loan_name,
                    'ref': reference,
                    'journal_id': journal_id,
                    'date': timenow,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
                record.account_move_id = move

            loan_line_id = False
            previous_ids = False
            remaining_ids = False
            if record.effective_date:
                loan_line_id = record.loan_id.loan_lines.filtered(lambda l: not l.operation_id and l.payment_date and l.payment_date.month == record.date_effective.month and l.state in ['draft', 'paid'])
                previous_ids = record.loan_id.loan_lines.filtered(lambda l: not l.operation_id and l.payment_date and l.payment_date <= record.date_effective and l.state in ['draft', 'paid'])
                remaining_ids = record.loan_id.loan_lines.filtered(lambda l: not l.operation_id and l.payment_date and l.payment_date > record.date_effective and l.state in ['draft', 'paid'])
                if loan_line_id:
                    loan_line_id = loan_line_id[0]
                    loan_line_id.operation_id = record.id
                if remaining_ids:
                    listed_remaining_ids = sorted(remaining_ids, key=lambda l: l.id)
                    record.next_schedule_id = listed_remaining_ids[0].id
            if not loan_line_id:
                raise UserError(_('There is no any installment are available.'))
            if record.loan_procedure_type == 'skip_installment' and record.date_effective:
                if loan_line_id:
                    last_id = sorted(record.loan_id.loan_lines, key=lambda k: k.id, reverse=True)
                    if last_id:
                        last_id = last_id[0]
                        new_line_id = last_id.copy(default={'payment_date': last_id.payment_date + relativedelta(months=1)})
                        last_id.amt = loan_line_id.amt
                    loan_line_id.state = 'skipped'
            elif record.loan_procedure_type == 'loan_payment' and record.date_effective and previous_ids and remaining_ids:
                amount = record.loan_id.loan_amt
                if record.payment_details == 'partially':
                    amount = record.payment_amt
                if loan_line_id:
                    diff_amount = amount - loan_line_id.amt
                    if len(previous_ids) == 1:
                        loan_line_id.amt = record.loan_id.loan_amt
                    else:
                        loan_line_id.amt = diff_amount
                    if record.payment_details == 'partially' and remaining_ids:
                        previous_amount = sum(previous_ids.mapped('amount'))
                        remaining_diff = record.loan_id.loan_amt - previous_amount - record.payment_amount
                        remaining_dff_avg = remaining_diff / len(remaining_ids)
                        for rl_id in remaining_ids:
                            rl_id.amt = remaining_dff_avg
                    elif record.payment_details == 'fully' and remaining_ids:
                        for rl_id in remaining_ids:
                            rl_id.state = 'cancel'
            elif record.loan_procedure_type == 'increase_amount' and record.date_effective and record.loan_amt:
                remaining_ids = record.loan_id.loan_lines.filtered(lambda l: l.payment_date and l.payment_date > record.date_effective and l.state in ['draft', 'paid'])
                if remaining_ids:
                    remaining_amount = sum(remaining_ids.mapped('amt'))
                    total_remaining_amount = record.loan_amt + remaining_amount
                    avg_remaining_amount = total_remaining_amount / len(remaining_ids)
                    for rl_id in remaining_ids:
                        rl_id.amt = avg_remaining_amount
        self.state = 'approve'

    def cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def refuse(self):
        self.ensure_one()
        self.state = 'refuse'

    def unlink(self):
        for record in self:
            if record.state not in ['draft', 'cancel']:
                raise ValidationError(
                    _('You cannot delete a request to Loan in  %s state.') % (record.state))
        return super(HrLoanProcedure, self).unlink()

    def refuse_loan_procedure(self):
        self.ensure_one()
        self.state = 'refuse'


    def apply_loan_procedure(self):
        if self._context.get('run_manually'):
            loan_procedure_ids = self
        else:
            loan_procedure_ids = self.env['loan.procedure'].search([('state', '=', 'approve'),
                                                                       ('date_effective', '=', fields.Date.today()),
                                                                       ('procedure_applied', '=', False),
                                                                       ('loan_procedure_type', 'in', ['increase_amount', 'loan_payment'])
                                                                       ])
        for record in loan_procedure_ids:
            if record.loan_procedure_type == 'increase_amount':
                loan_amount = record.loan_amt + record.loan_id.loan_amt
                record.loan_id.write({'loan_amt': loan_amount})
                if record.loan_id.emi_based_on == 'amount':
                    record.loan_id.date_due_calculation()
                else:
                    record.loan_id.amount_calculate()
                record.loan_id.with_context({'schedule_id': record.next_schedule_id}).calculate_increase_loan_amount()
                record.procedure_applied = True

            elif record.loan_procedure_type == 'loan_payment' and record.payment_type == 'by_account':
                amount = record.payment_amt
                if record.payment_details == 'fully':
                    amount = record.loan_id.loan_amot - record.loan_id.paid_amt
                slip_line_data = {'loan_id': record.loan_id.id, 'operation_id': record.id, 'employee_id': record.employee_id.id,
                                  'date': record.date_effective, 'amount': amount}
                installment_id = self.env['employee.installment.line'].create(slip_line_data)
                record.procedure_applied = True

            if self._context.get('run_manually') and record.loan_procedure_type == 'loan_payment' and record.payment_type == 'by_payslip':
                raise UserError("Payment type must be 'By Account'.")
