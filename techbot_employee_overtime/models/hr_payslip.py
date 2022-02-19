from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()
        for rec in self:
            rec.contract_id.overtime_ids.write({
                'is_used_payslip': True
            })
        return res
