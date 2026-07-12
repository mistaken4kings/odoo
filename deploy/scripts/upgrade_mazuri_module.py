#!/usr/bin/env python3
"""Replace legacy mazuri_connector with the unified mazuri Odoo app."""
from __future__ import annotations

import os
import xmlrpc.client


def main() -> None:
    url = os.environ.get("ODOO_URL", "http://127.0.0.1:8069").rstrip("/")
    db = os.environ.get("ODOO_DB", "mazuri")
    password = os.environ.get("ODOO_PASSWORD", "admin")
    user = os.environ.get("ODOO_USER", "admin")

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    models.execute_kw(db, uid, password, "ir.module.module", "update_list", [])

    legacy = models.execute_kw(
        db, uid, password,
        "ir.module.module", "search_read",
        [[["name", "=", "mazuri_connector"]]],
        {"fields": ["id", "state"], "limit": 1},
    )
    if legacy and legacy[0]["state"] == "installed":
        models.execute_kw(
            db, uid, password,
            "ir.module.module", "button_immediate_uninstall",
            [[legacy[0]["id"]]],
        )
        print("Uninstalled mazuri_connector")

    target = models.execute_kw(
        db, uid, password,
        "ir.module.module", "search_read",
        [[["name", "=", "mazuri"]]],
        {"fields": ["id", "state"], "limit": 1},
    )
    if not target:
        raise SystemExit(
            "mazuri module not found on this server. "
            "Deploy custom_addons/mazuri and restart Odoo first.",
        )
    if target[0]["state"] != "installed":
        models.execute_kw(
            db, uid, password,
            "ir.module.module", "button_immediate_install",
            [[target[0]["id"]]],
        )
        print("Installed mazuri")
    else:
        models.execute_kw(
            db, uid, password,
            "ir.module.module", "button_immediate_upgrade",
            [[target[0]["id"]]],
        )
        print("Upgraded mazuri")


if __name__ == "__main__":
    main()
