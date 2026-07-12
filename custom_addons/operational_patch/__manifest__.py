# -*- coding: utf-8 -*-
{
    "name": "Mazuri Operational Patch",
    "version": "18.0.1.0.0",
    "category": "Operations",
    "summary": "Review Mazuri staging proposals inside Odoo",
    "depends": ["base", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/operational_patch_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
