from odoo import models, fields, api, _
from datetime import datetime


class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _description = "Employee Overtime Management"
    _inherit = ['mail.thread']

    name = fields.Char('HR Overtime', )
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, )
    # state = fields.Selection([('draft', 'Draft'),
    #                           ('approve', 'Approved'),
    #                           ('done', 'Done'),
    #                           ('cancel', 'Cancelled')], string="Status", required=True, default='draft', tracking=True)
    date_overtime = fields.Date(string='Date', default=fields.Date.context_today)
    no_of_hr = fields.Integer(string='No of Hour')
    note = fields.Char('Description', required=True, )
    is_used_payslip = fields.Boolean(string="Is Used?")

    # @api.models
    # def create(self, vals):
    #     res = super(HrOvertime, self).create(vals)
    #     contract_id = self.env['hr.contract'].search([
    #         ('employee_id', '=', res.employee_id.id),
    #         ('state', '=', 'open'),
    #     ])
    #     if contract_id:
    #         contract_id.overtime_hours += res.no_of_hr
    #     return res
