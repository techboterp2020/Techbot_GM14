from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    @api.depends('employee_id')
    def _compute_overtime_hours(self):
        HrOvertime = self.env['hr.overtime']
        for rec in self:
            overtime_ids = HrOvertime.search([
                ('employee_id', '=', rec.employee_id.id),
                ('date_overtime', '>=', rec.date_start),
                ('date_overtime', '<=', rec.date_end),
                ('is_used_payslip', '=', False),
            ])
            rec.overtime_hours = sum(overtime_ids.mapped('no_of_hr')) or 0
            rec.overtime_ids = [(6, 0, overtime_ids.ids)]

    overtime_hours = fields.Float(string='Overtime Hour', compute="_compute_overtime_hours")
    overtime_ids = fields.Many2many('hr.overtime', compute="_compute_overtime_hours")
    overtime_rate = fields.Integer(string='Overtime Rate')
