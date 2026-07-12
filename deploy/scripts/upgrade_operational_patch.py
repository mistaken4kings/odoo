#!/usr/bin/env python3
"""Install operational_patch module alongside mazuri."""
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

    for name in ("operational_patch",):
        target = models.execute_kw(
            db, uid, password,
            "ir.module.module", "search_read",
            [[["name", "=", name]]],
            {"fields": ["id", "state"], "limit": 1},
        )
        if not target:
            print(f"{name} not found — deploy custom_addons/{name} first")
            continue
        state = target[0]["state"]
        if state == "installed":
            models.execute_kw(
                db, uid, password,
                "ir.module.module", "button_immediate_upgrade",
                [[target[0]["id"]]],
            )
            print(f"Upgraded {name}")
        else:
            models.execute_kw(
                db, uid, password,
                "ir.module.module", "button_immediate_install",
                [[target[0]["id"]]],
            )
            print(f"Installed {name}")


if __name__ == "__main__":
    main()
