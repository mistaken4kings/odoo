# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MazuriFinancing(models.Model):
    """A Mazuri-financed retailer order (Pay in 30, interest free).

    Records are created and updated by the Mazuri platform over the connected
    API user (XML-RPC), so distributors can reconcile embedded financing
    without leaving Odoo.
    """

    _name = 'mazuri.financing'
    _description = 'Mazuri financed order'
    _order = 'disbursed_at desc, id desc'

    name = fields.Char(string='Reference', required=True, index=True,
                       help='Mazuri order number, e.g. MZR-48213')
    org_id = fields.Char(string='Mazuri Org ID', index=True)
    retailer_name = fields.Char(string='Retailer')
    retailer_phone = fields.Char(string='Retailer Phone')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', ondelete='set null')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    principal = fields.Monetary(string='Financed Amount', currency_field='currency_id')
    payout_fee = fields.Monetary(string='Payout Fee', currency_field='currency_id')
    payout_total = fields.Monetary(string='Payout Total', currency_field='currency_id')
    payout_speed = fields.Selection([
        ('next_day', 'Next-day payout (5% fee)'),
        ('net_30', 'Pay in 30 (0% fee)'),
    ], string='Payout Speed', default='net_30')
    disbursed_at = fields.Datetime(string='Funds Released')
    due_date = fields.Date(string='Retailer Payment Due')
    state = fields.Selection([
        ('pending', 'Pending acceptance'),
        ('accepted', 'Accepted'),
        ('disbursed', 'Funds released'),
        ('repaid', 'Repaid'),
        ('overdue', 'Overdue'),
        ('declined', 'Declined'),
    ], string='Status', default='pending', index=True)
    notes = fields.Text()

    _sql_constraints = [
        ('name_org_unique', 'unique(name, org_id)',
         'A financing record already exists for this Mazuri order.'),
    ]

    @api.depends('name', 'retailer_name')
    def _compute_display_name(self):
        for record in self:
            if record.retailer_name:
                record.display_name = f"{record.name} — {record.retailer_name}"
            else:
                record.display_name = record.name
