# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from datetime import date
from odoo.exceptions import UserError
from num2words import num2words
from odoo.exceptions import ValidationError, Warning

class ProductProduct(models.Model):
    _inherit = 'product.product'

    part_no = fields.Char('Part No' )

ProductProduct()




class QualityControl(models.Model):
    _name = 'stock.quality.control'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _compute_count_check_pass(self):
        for rec in self:
            rec.count_check_pass = len(rec.quality_control_line.filtered(lambda q: q.check_pass))

    name = fields.Char('Name')
    count_check_pass = fields.Integer('Count', compute='_compute_count_check_pass')
    stock_picking_id = fields.Many2one('stock.picking')
    check_count = fields.Boolean('Check', default=False)
    quality_control_line = fields.One2many('stock.quality.control.line', 'quality_control_id')


    @api.model
    def create(self, values):
        rec = super(QualityControl, self).create(values)
        if 'company_id' in values:
            rec['name'] = self.env['ir.sequence'].with_context(force_company=values['company_id']).next_by_code(
                'quality_control') or _('New')
        else:
            rec['name'] = self.env['ir.sequence'].next_by_code('quality_control') or _('New')
        return rec

QualityControl()

class QualityControlLine(models.Model):
    _name = 'stock.quality.control.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    product_id = fields.Many2one('product.product')
    product_description = fields.Char('Product Description')
    od_no = fields.Char('OD')
    id_no = fields.Char('ID')
    cs_no = fields.Char('CS')
    thikness = fields.Char('Thikness')
    hardness = fields.Char('Hardness')
    apperance = fields.Char('Apperance')
    total_received = fields.Char('Total Received')
    total_accepted = fields.Char('Total Accepted')
    total_rejected = fields.Char('Total Rejected')
    batch_no = fields.Char('Batch No')
    check_pass = fields.Boolean('Pass/Fail', default=False)
    quality_control_id = fields.Many2one('stock.quality.control')
    stock_id = fields.Many2one('stock.picking')
    move_id = fields.Many2one('stock.move')

    def action_check_pass(self):
        for rec in self:
            rec.move_id.quantity_done += 1
            rec.check_pass = True

    def action_uncheck_pass(self):
        for rec in self:
            rec.move_id.quantity_done -= 1
            rec.check_pass = False



QualityControlLine()