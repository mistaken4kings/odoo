# -*- coding: utf-8 -*-
import logging
import secrets

from odoo import _, fields, http
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)

MAZURI_CLIENT_ID = 'mazuri-app'
API_LOGIN = 'mazuri_api'
API_NAME = 'Mazuri Integration API'


class MazuriConnectorController(http.Controller):

    @http.route('/mazuri/status', type='json', auth='public', csrf=False, methods=['POST'])
    def status(self):
        return {
            'installed': True,
            'version': '18.0.1.0.0',
            'client_id': MAZURI_CLIENT_ID,
        }

    @http.route('/mazuri/connect', type='http', auth='user', website=False, sitemap=False)
    def connect(self, client_id=None, redirect_uri=None, state=None, org_id=None, org_name=None, **kwargs):
        if client_id != MAZURI_CLIENT_ID:
            return request.render('mazuri_connector.connect_error', {
                'error': _('Unknown Mazuri application. Update the Mazuri Connector module.'),
            })
        if not redirect_uri or not redirect_uri.startswith(('https://', 'http://')):
            return request.render('mazuri_connector.connect_error', {
                'error': _('Invalid redirect URI.'),
            })

        if not request.env.user.has_group('base.group_system'):
            return request.render('mazuri_connector.connect_error', {
                'error': _('Only Odoo administrators can connect Mazuri.'),
            })

        return request.render('mazuri_connector.connect_authorize', {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'state': state or '',
            'org_id': org_id or '',
            'org_name': org_name or 'Mazuri',
            'user_name': request.env.user.name,
            'company_name': request.env.company.name,
        })

    @http.route('/mazuri/connect/approve', type='http', auth='user', methods=['POST'], csrf=True, website=False)
    def connect_approve(self, client_id=None, redirect_uri=None, state=None, org_id=None, org_name=None, **kwargs):
        if client_id != MAZURI_CLIENT_ID:
            raise AccessDenied(_('Invalid client.'))
        if not request.env.user.has_group('base.group_system'):
            raise AccessDenied(_('Administrator access required.'))

        Users = request.env['res.users'].sudo()
        api_user, api_password = self._ensure_api_user(Users)

        auth_code = request.env['mazuri.auth.code'].sudo().create_code({
            'org_id': org_id or '',
            'org_name': org_name or '',
            'redirect_uri': redirect_uri,
            'state': state or '',
            'client_id': client_id,
            'api_user_id': api_user.id,
            'api_login': api_user.login,
            'api_password': api_password,
        })

        Connection = request.env['mazuri.connection'].sudo()
        existing = Connection.search([('org_id', '=', org_id or ''), ('active', '=', True)], limit=1)
        connection_name = org_name or org_id or 'Mazuri'
        if existing:
            existing.write({
                'name': connection_name,
                'api_user_id': api_user.id,
                'api_login': api_user.login,
                'connected_by_id': request.env.user.id,
                'connected_at': fields.Datetime.now(),
            })
        else:
            Connection.create({
                'name': connection_name,
                'org_id': org_id or 'unknown',
                'org_name': org_name or '',
                'api_user_id': api_user.id,
                'api_login': api_user.login,
                'connected_by_id': request.env.user.id,
            })

        from werkzeug.urls import url_encode
        params = url_encode({'code': auth_code.code, 'state': state or ''})
        separator = '&' if '?' in redirect_uri else '?'
        return request.redirect(f'{redirect_uri}{separator}{params}')

    @http.route('/mazuri/oauth/token', type='json', auth='public', csrf=False, methods=['POST'])
    def oauth_token(self, grant_type=None, code=None, redirect_uri=None, client_id=None, client_secret=None, **kwargs):
        if grant_type != 'authorization_code':
            return {'error': 'unsupported_grant_type'}
        if client_id != MAZURI_CLIENT_ID:
            return {'error': 'invalid_client'}
        if not client_secret:
            return {'error': 'invalid_client'}

        expected_secret = request.env['ir.config_parameter'].sudo().get_param(
            'mazuri.client_secret', '',
        )
        if not expected_secret or client_secret != expected_secret:
            return {'error': 'invalid_client'}

        AuthCode = request.env['mazuri.auth.code'].sudo()
        record = AuthCode.search([('code', '=', code)], limit=1)
        if not record:
            return {'error': 'invalid_grant'}

        try:
            record.consume(client_id, redirect_uri)
        except UserError as error:
            return {'error': 'invalid_grant', 'error_description': str(error)}

        api_password = record.api_password
        record.write({'api_password': False})

        base_url = request.httprequest.url_root.rstrip('/')
        return {
            'access_type': 'xmlrpc',
            'url': base_url,
            'database': request.env.cr.dbname,
            'username': record.api_login,
            'password': api_password,
            'org_id': record.org_id,
            'org_name': record.org_name,
        }

    def _ensure_api_user(self, Users):
        api_password = secrets.token_urlsafe(24)
        user = Users.search([('login', '=', API_LOGIN)], limit=1)
        group_ids = self._api_group_ids()

        if user:
            user.write({
                'name': API_NAME,
                'password': api_password,
                'active': True,
                'groups_id': [(6, 0, group_ids)],
            })
            return user, api_password

        user = Users.create({
            'name': API_NAME,
            'login': API_LOGIN,
            'password': api_password,
            'groups_id': [(6, 0, group_ids)],
        })
        return user, api_password

    def _api_group_ids(self):
        xmlids = [
            'base.group_user',
            'stock.group_stock_user',
            'sales_team.group_sale_salesman',
        ]
        group_ids = []
        for xmlid in xmlids:
            group = request.env.ref(xmlid, raise_if_not_found=False)
            if group:
                group_ids.append(group.id)
        return group_ids
