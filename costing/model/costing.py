# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from datetime import date
from odoo.exceptions import UserError
from num2words import num2words
from odoo.exceptions import ValidationError, Warning


class product_costing(models.Model):
    _name = 'product.costing'
    _description = "Product Costing"
    _order = 'name desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']


    name = fields.Char(string='Sample Receipt No', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    crm_sequence = fields.Char('CRM Sequence',store=True)
    crm_ref = fields.Char('CRM Ref',store=True)
    date = fields.Date('Date',store=True)
    notes_crm = fields.Text('Estimate Description',store=True)
    tags_ids = fields.Many2many('crm.tag',string='Tags',help='Please read the tags and description,then choose the required materials')
    product_estimate_lines = fields.One2many('product.estimate.lines','costing_id')
    status = fields.Selection([('draft','Draft'),
                               ('confirm','Confirm')],string="Status",default='draft')
    margin = fields.Float('Margin', tracking=True)
    total_cost = fields.Float('Total Cost', compute='calculate_total_estimated')
    sale_order_confrim = fields.Boolean('Sale Order Confirmed',default=False)
    expected_delivery = fields.Date('Expected Delivery') 
    # required=True

    #questionairre
    site_visit = fields.Selection([('YES', 'Yes'),
                                   ('NO', 'No')], string="Site Visit Required ?", required=True)
    technical_visit = fields.Selection([('YES', 'Yes'),
                                        ('NO', 'No')], string="Technical Visit Required ?", required=True)
    location = fields.Char('Location', required=True)
    poc = fields.Char('Point Of Contact', required=True)
    contact_no = fields.Char('Contact No/Email', required=True)
    permission = fields.Selection([('YES', 'Yes'),
                                   ('NO', 'No')], string="Permission Required ?", required=True)
    boom_lift = fields.Selection([('YES', 'Yes'),
                                  ('NO', 'No')], string="Boom lift Required ?", required=True)
    boom_lift_desc = fields.Text('Describe the need of Boom Lift')

    # for sales order page:
    sale_id = fields.Many2one('sale.order','Sale Order')
    salesperson_id = fields.Many2one('res.users','Sales Person')

    #for counting the number of line item
    production_count = fields.Integer('Manufacturing', compute='get_production_count')
    sales_count = fields.Integer('Sales', compute='get_production_count')

    def get_production_count(self):
        count_production = self.env['mrp.production'].search_count([('sale_id', '=', self.sale_id.id)])
        count_sales = self.env['sale.order'].search_count([('id', '=', self.sale_id.id)])
        self.production_count = count_production
        self.sales_count = count_sales

    def costing_to_manufacture_smart_button(self):
        return {
            'name': _('Manufacturing'),
            'domain': [('sale_id', '=', self.sale_id.id)],
            'view_type': 'form',
            'res_model': 'mrp.production',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }

    def costing_to_sale_smart_button(self):
        if self.sale_id.id:
            return {
                'name': _('Sales'),
                'domain': [('id', '=', self.sale_id.id)],
                'view_type': 'form',
                'res_model': 'sale.order',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window'
            }


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.costing') or 'New'
        result = super(product_costing, self).create(vals)
        return result

    @api.depends('product_estimate_lines.cost', 'margin')
    def calculate_total_estimated(self):
        for order in self:
            amount = 0.0
            extra_amt = self.margin
            for line in order.product_estimate_lines:
                amount += line.cost
            order.update({
                'total_cost': amount + extra_amt
            })

    def reset_button(self):
        self.status = 'draft'
        crm_estimate = self.env['crm.lead'].search([('crm_sequence', '=', self.crm_sequence)])
        for data in crm_estimate:
            data.estimate = False

    def confirm_button(self):
        if len(self.product_estimate_lines) == 0:
            raise Warning(_('Please Fill Line Details'))
        else:
            self.status = 'confirm'
            crm_estimate = self.env['crm.lead']
            # .search([('crm_sequence','=',self.crm_sequence)])
            for data in crm_estimate:
                data.estimate = True

    def create_manufacturing_orders(self):
        val1 = {}
        for rec in self:
            main_products = rec.env['product.estimate.lines'].search([('costing_id','=',rec.id),('is_manufacturing','=',True)])
            for products in main_products:
                bom_list = [(5, 0, 0)]
                for bom_item in products.estimate_product_ids:
                    if products.id == bom_item.product_bom_id.id:
                        val1 = {
                            'product_id': bom_item.product_id.id,
                            'product_uom': bom_item.uom_id.id,
                            'product_uom_qty': bom_item.qty,
                            'name': 'From Crm',
                            'location_dest_id': 15,
                            'location_id': 8,
                            'company_id': 1,
                        }
                    bom_list.append((0, 0, val1))
                manufacturing = self.env['mrp.production'].create({
                    'estimate_sequence': products.id,
                    'sale_id': products.costing_id.sale_id.id,
                    'product_id': products.name.id,
                    'product_uom_id': products.uom_id.id,
                    'product_qty': products.qty,
                    'move_raw_ids': bom_list
                })


class product_cost_lines(models.Model):
    _name ='product.estimate.lines'
    _description = 'Cost Details'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'estimate_sequence desc'

    costing_id = fields.Many2one('product.costing','Costing ID')
    crm_sequence = fields.Char('CRM Sequence', store=True,compute='map_crm_sequence')
    estimate_sequence = fields.Char('Estimate Sequence', store=True,compute='map_crm_sequence')

    main_product_id = fields.Many2one('product.product','Main Product')
    name = fields.Many2one('product.product','Product for estimation')
    qty = fields.Float('Quantity',default='1.00')
    uom_id = fields.Many2one('uom.uom','UoM')
    cost = fields.Float('Cost')
    margin = fields.Float('Margin',tracking=True)
    total_cost = fields.Float('Total Cost',compute='calculate_total_estimated')
    status = fields.Selection([('draft', 'Draft'),
                               ('confirm', 'Confirm')], string="Status", default='draft', compute='map_crm_sequence')

    estimate_product_ids = fields.One2many('product.bom.lines','product_bom_id','Product BOM')
    mo_done = fields.Boolean('MO Created',default=False)
    so_done = fields.Boolean('SO Created',default=False)
    confirm_product = fields.Boolean('Confirm Product',help="Enable this to see the default mapping of products from inventory BOM for 1 main product")
    is_manufacturing = fields.Boolean('For Manufacturing',default=True)

    @api.onchange('confirm_product','name')
    def map_bom_lines(self):
        line = [(5, 0, 0)]
        val = {}
        for data in self:
            bom_line = data.env['product.crm.lines'].search([('crm_id', '=', data.name.id)])
            for rec in bom_line:
                val = {
                    'product_id':rec.direct_material_id.id,
                    'prod_length':rec.height,
                    'prod_breadth':rec.width,
                    'qty':rec.qty,
                    'uom_id':rec.uom_id.id,
                    'cost':rec.total_cost,
                    'proposed_cost':rec.total_cost
                }
                line.append((0, 0, val))
            #print(line)
            data.estimate_product_ids = line

    def name_get(self):
        res = []
        quote_name = ''
        for record in self:
            if record.name:
                quote_name = record.name.name + ", " + str(record.crm_sequence)
            res.append((record.id, quote_name))
        return res

    @api.depends('costing_id')
    def map_crm_sequence(self):
        for rec in self:
            rec.crm_sequence = rec.costing_id.crm_sequence
            #print(rec.costing_id.name,'*****************')
            # rec.estimate_sequence = rec.costing_id.name
            rec.status = rec.costing_id.status

    @api.onchange('name','qty')
    def map_uom_cost(self):
        for i in self:
            i.uom_id =  i.name.uom_id.id
            i.cost =  i.qty * i.total_cost

    @api.depends('estimate_product_ids.proposed_cost', 'margin')
    def calculate_total_estimated(self):
        for order in self:
            amount = 0.0
            extra_amt = order.margin
            for line in order.estimate_product_ids:
                amount += line.proposed_cost

            order.update({
                'total_cost': amount + extra_amt,
                'cost': amount + extra_amt
            })


class product_estimate_bom_lines(models.Model):
    _name = 'product.bom.lines'
    _description = 'BOM Details'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'crm_sequence desc'

    product_bom_id = fields.Many2one('product.estimate.lines','Product Estimate')
    crm_sequence = fields.Char('CRM Sequence',compute='map_crm',store=True)
    product_id = fields.Many2one('product.product', 'Product for estimation',required=True)
    prod_length = fields.Float('Length',default='1.00')
    prod_breadth = fields.Float('Breadth',default='1.00')
    qty = fields.Float('Quantity',compute='calc_qty',default='1.00',tracking=True,store=True)
    uom_id = fields.Many2one('uom.uom', 'UoM',tracking=True)
    cost = fields.Float('Cost',tracking=True)
    proposed_cost = fields.Float('Proposed Cost',tracking=True)
    status = fields.Selection([('draft', 'Draft'),
                               ('confirm', 'Confirm')], string="Status", default='draft',compute='map_crm')

    @api.onchange('product_id', 'qty')
    def map_uom_cost(self):
        for i in self:
            i.uom_id = i.product_id.uom_id.id
            i.proposed_cost  = i.cost
            # i.cost = i.product_id.list_price * i.qty


    @api.depends('product_bom_id')
    def map_crm(self):
        for i in self:
            i.crm_sequence = i.product_bom_id.costing_id.crm_sequence
            i.status = i.product_bom_id.costing_id.status

    @api.depends('prod_length','prod_breadth')
    def calc_qty(self):
        for i in self:
            i.qty = i.prod_length * i.prod_breadth

class Inherit_CRM(models.Model):
    _inherit = 'crm.lead'
    sent_estimate = fields.Boolean('Estimation',default=False)
    estimate = fields.Boolean('Estimation',default=False)
    saleperson_product_line = fields.One2many('crm.product.lines', 'crm_product_id','Sale Products')
    site_visit = fields.Selection([('YES', 'Yes'),
                                   ('NO', 'No')], string="Site Visit Required ?", required=True)
    technical_visit = fields.Selection([('YES', 'Yes'),
                                        ('NO', 'No')], string="Technical Visit Required ?", required=True)
    permission = fields.Selection([('YES', 'Yes'),
                                   ('NO', 'No')], string="Permission Required ?", required=True)
    boom_lift = fields.Selection([('YES', 'Yes'),
                                  ('NO', 'No')], string="Boom lift Required ?", required=True)


    def send_to_estimate(self):
        prod_list = [(5, 0, 0)]
        val = {}
        for rec in self:
            for data in rec.saleperson_product_line:
                val = {
                    'name':data.direct_material_id.id,
                    'uom_id':data.uom_id.id,
                    'qty' :data.qty,
                }
                prod_list.append((0, 0, val))
        print(prod_list,"#############################")
        self.sent_estimate = True
        estimate_order = self.env['product.costing'].create({
        #     'crm_sequence': self.crm_sequence,
            'crm_ref': self.name,
            'tags_ids': self.tag_ids,
            'notes_crm':self.description,
            'date' : date.today(),
            'site_visit' : self.site_visit,
            'technical_visit' : self.technical_visit,
            'location' : self.partner_id.state_id.name,
            'poc' : self.partner_id.name,
            'contact_no' : self.phone,
            'permission' : self.permission,
            'boom_lift' : self.boom_lift,
            # 'boom_lift_desc' : self.boom_lift_desc,
            'expected_delivery' : self.date_deadline,
            'product_estimate_lines' :  prod_list
        #
        })
        print(estimate_order, 10*"AJMAL")

class Costing_CRM_BOM_lines(models.Model):
    _name = 'crm.product.lines'

    crm_product_id = fields.Many2one('crm.lead','CRM Product')
    direct_material_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom', 'Unit',required=True,related='direct_material_id.uom_id')
    qty = fields.Float('QTY',required=True,default=1.00)

class Inherit_Sales(models.Model):
    _inherit = 'sale.order'


    def _get_crm_sequence(self):
        domain = [('id', '=', -1)]
        employee_list = []
        some_model = self.env['crm.lead'].search([('estimate', '=', True)])
        for each in some_model:
            print(each.id)
            employee_list.append(each.id)
        if employee_list:
            domain = [('id', 'in', employee_list)]
            return domain
        return domain

    crm_sequence = fields.Many2one('crm.lead', 'CRM Sequence',domain=_get_crm_sequence)
    estimate_sequence = fields.Char('Estimate Sequence')
    estimate_sequence_id = fields.Integer('Estimate Sequence')
    production_count = fields.Integer('Count',compute='get_production_count')


    # @api.onchange('crm_sequence')
    # def _check_existing_crm_sequence(self):
    #     for rec in self:
    #         sale_order_crm_sequence = rec.env['sale.order'].search([('crm_sequence','=',rec.crm_sequence.id)]).name
    #         if sale_order_crm_sequence:
    #             raise UserError(_(
    #                 'It is already used in %s'
    #             ) % (sale_order_crm_sequence))

    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()

        if self.state == 'sale' or self.state == 'done':
            sale_order_confirmation = self.env['product.costing'].search([('crm_sequence','=',self.crm_sequence.crm_sequence)])
            for conf in sale_order_confirmation:
                self.estimate_sequence = conf.name
                self.estimate_sequence_id = conf.id
                conf.sale_order_confrim = True
                conf.sale_id = self.id
                conf.salesperson_id = self.user_id
                conf.create_manufacturing_orders()
            template_id = self.env.ref('costing.email_template_confirmation_report').id
            template = self.env['mail.template'].browse(template_id)
            template.send_mail(self.id, force_send=True)
        return True



    def get_production_count(self):
        count = self.env['mrp.production'].search_count([('sale_id','=',self.id)])
        self.production_count = count

    @api.onchange('crm_sequence')
    def map_order_lines(self):
        for rec in self:
            # sale_order_crm_sequence = rec.env['sale.order'].search([('crm_sequence', '=', rec.crm_sequence.id)])
            # print(sale_order_crm_sequence, "%%%%%%%%%%%%%%%%")
            # if sale_order_crm_sequence:
            #     for name in sale_order_crm_sequence:
            #         raise UserError(_(
            #                         'It is already used in %s'
            #                     ) % (name.name))
            # else:
            rec.partner_id = rec.crm_sequence.partner_id
            crm_lines = rec.env['product.costing'].search([('crm_sequence', '=', rec.crm_sequence.crm_sequence)])
            main_list = [(5, 0, 0)]
            val = {}
            for prod_id in crm_lines:
                for line in prod_id.product_estimate_lines:
                    val = {
                        'product_id': line.name.id,
                        'product_uom_qty': line.qty,
                        'product_uom': line.uom_id,
                        'price_unit': line.cost / line.qty,
                    }
                    main_list.append((0, 0, val))
            rec.update({
                'order_line': main_list
            })


    #
    # def send_mail_production(self):
    #     if self.state == 'sale' or self.state == 'done':
    #         sale_order_confirmation = self.env['product.costing'].search([('crm_sequence','=',self.crm_sequence.crm_sequence)])
    #         for conf in sale_order_confirmation:
    #             self.estimate_sequence = conf.name
    #             self.estimate_sequence_id = conf.id
    #             conf.sale_order_confrim = True
    #             conf.sale_id = self.id
    #             conf.salesperson_id = self.user_id
    #
    #         template_id = self.env.ref('costing.email_template_confirmation_report').id
    #         template = self.env['mail.template'].browse(template_id)
    #         template.send_mail(self.id, force_send=True)

    def costing_to_manufacture_smart_button(self):
        return {
            'name': _('Manufacturing'),
            'domain': [('sale_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'mrp.production',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window'
        }


class Inherit_Product_Product(models.Model):
    _inherit = 'product.product'

    available_for_estimate = fields.Boolean('Available For Estimate')
    product_crm_ids = fields.One2many('product.crm.lines', 'crm_id', required=True)
    height = fields.Float('Height')
    width = fields.Float('Width')
    area_per_unit = fields.Float('Area Per Unit',compute='map_total_area',store=True)
    area_available = fields.Float('Total Area Of Products', compute='map_area_available',store=True)

    @api.depends('qty_available','area_per_unit')
    def map_area_available(self):
        for rec in self:
            if rec.qty_available >= 0 and rec.area_per_unit > 0:
                rec.area_available = rec.qty_available * rec.area_per_unit
            else:
                rec.area_available = 0.0

    @api.depends('height','width')
    def map_total_area(self):
        for rec in self:
            rec.area_per_unit = rec.height * rec.width


class Costing_CRM_Lines(models.Model):
    _name = 'product.crm.lines'

    crm_id = fields.Many2one('product.product')

    direct_material_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('uom.uom', 'Unit')
    width = fields.Float('Width')
    height = fields.Float('Height')
    area = fields.Float('Area')
    qty = fields.Float('QTY')
    cost = fields.Float('Cost',related='direct_material_id.standard_price')
    total_cost = fields.Float('Total Cost',compute='map_total_cost',store=True)

    @api.onchange('height','width')
    def calc_area(self):
        for rec in self:
            rec.area = rec.width * rec.height
            if rec.direct_material_id.area_per_unit > 0:
                rec.qty = rec.area / rec.direct_material_id.area_per_unit
            else:
                rec.qty = 0.0

    @api.onchange('area')
    def calc_qty(self):
        for rec in self:
            if rec.direct_material_id.area_per_unit > 0:
                rec.qty = rec.area/rec.direct_material_id.area_per_unit

            rec.total_cost = rec.qty * rec.cost

    @api.depends('qty')
    def map_total_cost(self):
        for rec in self:
            rec.total_cost = rec.qty * rec.cost

    @api.onchange('direct_material_id')
    def map_units_area(self):
        self.uom_id = self.direct_material_id.uom_id.id
        # self.width = self.direct_material_id.width
        # self.height = self.direct_material_id.height
        # self.area = self.direct_material_id.area_per_unit


class Inherit_MRP_Production(models.Model):
    _inherit = 'mrp.production'

    estimate_sequence = fields.Many2one('product.estimate.lines','Estimate Sequence')
    sale_id = fields.Many2one('sale.order', 'Sale Order')

    @api.onchange('estimate_sequence')
    def confirm_cr(self):
        self.product_id = self.estimate_sequence.name.id
        self.product_qty = self.estimate_sequence.qty
        print("self.estimate_sequence.uom_id.id",self.estimate_sequence.uom_id.id)
        self.product_uom_id = self.estimate_sequence.uom_id.id

    @api.onchange('product_id', 'picking_type_id', 'company_id')
    def onchange_product_id(self):
        line = [(5, 0, 0)]
        val = {}
        if self.product_id:
            for rec in self:
                for lines in rec.estimate_sequence.estimate_product_ids:
                    print(lines.product_id.name,"##########################")
                    print(lines.crm_sequence,"##########################")
                    print(rec.estimate_sequence.crm_sequence,"##########################")
                    print(rec.product_id,"##########################")
                    print(lines.product_bom_id.name.id,"##########################")
                    if lines.crm_sequence == rec.estimate_sequence.crm_sequence and rec.product_id.id == lines.product_bom_id.name.id:
                        val = {
                            'product_id' : lines.product_id.id,
                            'product_uom' : lines.uom_id.id,
                            'product_uom_qty' : lines.qty,
                            'name' : 'From Crm',
                            'location_dest_id' : 15,
                            'location_id' : 8,
                            'company_id' : 1,
                        }
                        line.append((0, 0, val))
                        print(val,"@##$#$$$$$$$$$$$$$$$$$$$")
                rec.move_raw_ids = line
                # rec.update({
                #     'move_raw_ids': line
                # })

        else:
            """ Finds UoM of changed product. """
            if not self.product_id:
                self.bom_id = False
            elif not self.bom_id or self.bom_id.product_tmpl_id != self.product_tmpl_id or (
                    self.bom_id.product_id and self.bom_id.product_id != self.product_id):
                bom = self.env['mrp.bom']._bom_find(product=self.product_id, picking_type=self.picking_type_id,
                                                    company_id=self.company_id.id, bom_type='normal')
                if bom:
                    self.bom_id = bom.id
                    self.product_qty = self.bom_id.product_qty
                    self.product_uom_id = self.bom_id.product_uom_id.id
                else:
                    self.bom_id = False
                    self.product_uom_id = self.product_id.uom_id.id


class CostingStockMove(models.Model):
    _inherit = 'stock.move'

    # def unlink(self):
    #     res = super(CostingStockMove, self).unlink()
    #     if any(move.state not in ('draft','confirmed','assigned','done','cancel','waiting','partially_available') for move in self):
    #         raise UserError(_(' draft moves.'))
    #     # With the non plannified picking, draft moves could have some move lines.
    #     self.with_context(prefetch_fields=False).mapped('move_line_ids').sudo.unlink()
    #     return res
