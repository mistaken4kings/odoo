import os
import secrets

from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    secret = os.environ.get('ODOO_MAZURI_CLIENT_SECRET', '').strip()
    if not secret:
        secret = secrets.token_urlsafe(32)
    env['ir.config_parameter'].sudo().set_param('mazuri.client_secret', secret)
    env['ir.config_parameter'].sudo().set_param('mazuri.client_id', 'mazuri-app')
