# -*- coding: utf-8 -*-
import logging
import pprint
import requests
import werkzeug
import json
import time
import base64


from odoo import http, SUPERUSER_ID
from odoo.http import request


_logger = logging.getLogger(__name__)


class HyloController(http.Controller):

    @http.route(['/hylo/checkout'], type='http', auth='none', csrf=None, website=True)
    def checkout(self, **post):
        _logger.info('Hylo datas %s', pprint.pformat(post))  # debug
        cr, uid, context, env = request.cr, SUPERUSER_ID, request.context, request.env
        acquirer = env['payment.acquirer'].sudo().browse(eval(post.get('acquirer')))
        currency = env['res.currency'].sudo().browse(eval(post.get('currency_id'))).name
        if currency not in ['INR', 'AED']:
            _logger.info("Invalid parameter 'currency' expected one of: 'INR', 'AED'")
            return request.redirect('/shop/cart')
        url = "http://52.163.215.147:1026/Api/v1.0/Payment" if acquirer.state == 'test' \
            else "https://hylo.biz/Api/v1.0/Payment"

        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return_url = base_url + '/hylo/checkout/confirm'
        redirect_url = return_url
        payload = {
            "orderId" : post.get('reference'),
            "amount": str(post.get('amount')),
            "customer_name": str(post.get('partner_name')),
            "customer_mobile": str(post.get('partner_phone')),
            "customer_email": str(post.get('partner_email')),
            "currency": post.get('currency'),
            "expire_by": 0,
            "sms_notify": True,
            "email_notify":True,
            "partial_payment":False,
            "redirect_url": redirect_url
        }

        user = acquirer.hylo_merchant_id
        password = acquirer.hylo_merchant_key
        userpass = user + ':' + password
        encoded_u = base64.b64encode(userpass.encode()).decode()
        headers = {"Authorization": "Basic %s" % encoded_u,
                   'Content-Type': 'application/json'}

        data = json.dumps(payload)
        response = requests.request("POST", url, headers=headers, data=data)
        vals = json.loads(response.text)
        _logger.info(pprint.pformat(vals))
        return werkzeug.utils.redirect(vals.get('short_url'))

    @http.route(['/hylo/checkout/confirm'], type='http', auth='none', csrf=None, website=True)
    def checkout_confirm(self, **post):

        env,context = request.env ,request.context
        tx_id = request.session.get('__website_sale_last_tx_id')
        sale_order_id =request.session.get('sale_order_id')
        tx =env['payment.transaction'].sudo().browse(tx_id)
        acquirer = env['payment.acquirer'].sudo().search([('provider', '=', 'hylo')])
        url = "http://52.163.215.147:1026/Api/v1.0/CheckPaymentStatus" if acquirer and acquirer.state == 'test' \
            else "https://hylo.biz/Api/v1.0/Payment"
        user = acquirer.hylo_merchant_id
        password = acquirer.hylo_merchant_key
        userpass = user + ':' + password
        encoded_u = base64.b64encode(userpass.encode()).decode()
        headers = {"Authorization": "Basic %s" % encoded_u,
                   'Content-Type': 'application/json'}
        tx.sudo().hylo_checkout_id = post.get('order_id')

        tx.sudo().sale_order_id = sale_order_id
        payload = {
            "orderId": str(post.get('order_id'))
        }
        data = json.dumps(payload)
        response = requests.request("GET", url, data=data, headers=headers)
        vals = json.loads(response.text)

        _logger.info(pprint.pformat(vals))
        if vals.get('status') == 'APPROVED':
            tx.state = 'done'
            tx.hylo_checkout_id = vals.get('referenceId')
            tx.sale_order_id.with_context(dict(context, send_email=True)).action_confirm()
            return request.redirect('/shop/payment/validate')
        elif vals.get('status') != 'APPROVED':
            tx.state = 'error'
            return request.redirect('/shop')

