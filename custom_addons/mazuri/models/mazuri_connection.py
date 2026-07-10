# -*- coding: utf-8 -*-
from odoo import fields, models


class MazuriConnection(models.Model):
    _name = 'mazuri.connection'
    _description = 'Active Mazuri integration'
    _order = 'connected_at desc'

    name = fields.Char(required=True)
    org_id = fields.Char(required=True, index=True)
    org_name = fields.Char()
    api_user_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    api_login = fields.Char(required=True)
    connected_at = fields.Datetime(default=fields.Datetime.now)
    connected_by_id = fields.Many2one('res.users', string='Connected By')
    active = fields.Boolean(default=True)
    last_sync_at = fields.Datetime()
