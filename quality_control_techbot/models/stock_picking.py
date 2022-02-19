# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from datetime import date
from odoo.exceptions import UserError
from num2words import num2words
from odoo.exceptions import ValidationError, Warning


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    doc_no = fields.Char('Doc No')
    st_doc_no = fields.Char('ST Doc No')
    qc_line = fields.One2many('stock.quality.control', 'stock_picking_id')
    tick = fields.Boolean('Tick', default=False)

    def check_qcl_action(self):
        print("TEST")
        qc_obj = self.env['stock.quality.control']
        qc_line_obj = self.env['stock.quality.control.line']
        for rec in self:
            if rec.tick == False:
                qc_line_val=[]
                for l in rec.move_ids_without_package:
                    for p in range(int(l.no_of_ratio)):
                        qc_line_val.append((0, 0, {
                            'product_id': l.product_id.id,
                            'move_id' : l.id
                        }))
                qc_id = qc_obj.create({'stock_picking_id': self.id,
                                       'name': self.name,
                                       'quality_control_line' : qc_line_val
                                       })

                rec.write({
                    'tick' : True
                })

            return {
                'name': _("Quality Control"),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.quality.control',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': qc_id.id,

            }

StockPicking()


class StockMove(models.Model):
    _inherit = 'stock.move'

    no_of_ratio = fields.Char('No of Ratio')

