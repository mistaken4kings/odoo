# -*- coding: utf-8 -*-
from odoo import fields, models


class OperationalPatch(models.Model):
    _name = "operational.patch"
    _description = "Mazuri operational staging patch"
    _order = "create_date desc"

    name = fields.Char(required=True, index=True)
    mazuri_proposal_id = fields.Char(string="Mazuri Proposal ID", index=True)
    mazuri_org_id = fields.Char(string="Mazuri Org ID", index=True)
    title = fields.Char()
    summary = fields.Text()
    patch_payload = fields.Text(string="Patch JSON")
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("review", "In Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("merged", "Merged"),
        ],
        default="review",
        required=True,
    )

    def action_approve(self):
        for record in self:
            record.state = "approved"
        return True

    def action_reject(self):
        for record in self:
            record.state = "rejected"
        return True
