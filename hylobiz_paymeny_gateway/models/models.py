################################################################

import logging
from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class Hylo(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('hylo', 'Hylo')], ondelete={'hylo': 'set default'})
    hylo_merchant_id = fields.Char('Merchant ID', required_if_provider='Hylo',
                                   groups='base.group_user')
    hylo_merchant_key = fields.Char('Merchant Key', required_if_provider='Hylo',
                                    groups='base.group_user')


    def _get_hylo_urls(self):
        """ Paytm URLs"""
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        return_url = base_url + '/hylo/checkout'

        return {'hylo_form_url': return_url}

    def hylo_get_form_action_url(self):
        return self._get_hylo_urls()['hylo_form_url']

    def hylo_form_generate_values(self, values):
        hylo_tx_values = dict(values)
        hylo_tx_values.update({
            'hylo': self.hylo_get_form_action_url(),
            'tx_url': self.hylo_get_form_action_url()
        })
        return hylo_tx_values


class HyloTransaction(models.Model):
    _inherit = "payment.transaction"

    hylo_checkout_id = fields.Char("Hylo Checkout Id")
    acquirer_name = fields.Selection(related='acquirer_id.provider')
    sale_order_id =fields.Many2one('sale.order')
