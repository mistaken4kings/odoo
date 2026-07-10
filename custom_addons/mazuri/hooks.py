import os
import secrets

from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    secret = os.environ.get('ODOO_MAZURI_CLIENT_SECRET', '').strip()
    if not secret:
        secret = secrets.token_urlsafe(32)
    env['ir.config_parameter'].sudo().set_param('mazuri.client_secret', secret)
    env['ir.config_parameter'].sudo().set_param('mazuri.client_id', 'mazuri-app')
    _ensure_pay_in_30_term(env)


def _ensure_pay_in_30_term(env):
    """Install the 'Mazuri Pay in 30 (interest free)' payment term."""
    PaymentTerm = env['account.payment.term'].sudo()
    if PaymentTerm.search([('name', '=', 'Mazuri Pay in 30 (interest free)')], limit=1):
        return
    PaymentTerm.create({
        'name': 'Mazuri Pay in 30 (interest free)',
        'note': 'Retailer pays 30 days after order, financed by Mazuri. 0% interest.',
        'line_ids': [(0, 0, {
            'value': 'percent',
            'value_amount': 100.0,
            'nb_days': 30,
        })],
    })
