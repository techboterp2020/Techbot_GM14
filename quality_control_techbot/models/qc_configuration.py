# -*- coding: utf-8 -*-
from odoo import api, fields, models, _



class QCConfiguration(models.Model):
    _name = 'qc.configuration'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')
    qc_config_line_ids = fields.One2many(
        'qc.configuration.line', 'qc_config_id', "QC Configuration Lines")

QCConfiguration()

class QCConfigurationLine(models.Model):
    _name = 'qc.configuration.line'

    left_operator = fields.Selection([('greterthan', '>'),
                                      ('lessthan', '<'),
                                      ('greterthanequal', '>='),
                                      ('lessthanequal', '<=')])
    start_from = fields.Float("Start From (in %)")
    between_operator = fields.Selection([('greterthan', '>'),
                                      ('lessthan', '<'),
                                      ('greterthanequal', '>='),
                                      ('lessthanequal', '<=')])
    end_to = fields.Float("End TO")
    qc_config_id = fields.Many2one("qc.configuration", "QC Config")
    no_of_items = fields.Float("No of Item")

QCConfigurationLine()