# -*- coding: utf-8 -*-
import secrets
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class MazuriAuthCode(models.Model):
    _name = 'mazuri.auth.code'
    _description = 'Mazuri OAuth authorization code'
    _order = 'create_date desc'

    code = fields.Char(required=True, index=True)
    org_id = fields.Char(string='Mazuri Org ID')
    org_name = fields.Char(string='Mazuri Org Name')
    redirect_uri = fields.Char(required=True)
    state = fields.Char()
    client_id = fields.Char()
    expires_at = fields.Datetime(required=True)
    used = fields.Boolean(default=False)
    api_user_id = fields.Many2one('res.users', ondelete='set null')
    api_login = fields.Char()
    api_password = fields.Char(help='Single-use; cleared after token exchange')

    @api.model
    def _cleanup_expired(self):
        cutoff = fields.Datetime.now() - timedelta(hours=24)
        expired = self.search([
            '|',
            ('expires_at', '<', fields.Datetime.now()),
            ('create_date', '<', cutoff),
        ])
        expired.unlink()

    @api.model
    def create_code(self, values):
        self._cleanup_expired()
        code = secrets.token_urlsafe(32)
        expires_at = fields.Datetime.now() + timedelta(minutes=10)
        return self.create({
            **values,
            'code': code,
            'expires_at': expires_at,
        })

    def consume(self, client_id, redirect_uri):
        self.ensure_one()
        if self.used:
            raise UserError('Authorization code already used.')
        if self.expires_at < fields.Datetime.now():
            raise UserError('Authorization code expired.')
        if self.client_id and self.client_id != client_id:
            raise UserError('Invalid client.')
        if self.redirect_uri != redirect_uri:
            raise UserError('Redirect URI mismatch.')
        self.used = True
        return self
