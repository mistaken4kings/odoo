#!/usr/bin/env python3
"""Create Mazuri API user + OAuth application for Nango odoo-cc."""
from __future__ import annotations

import argparse
import os
import secrets
import xmlrpc.client


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--admin-user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--admin-password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--api-login", default="mazuri_api")
    parser.add_argument("--api-name", default="Mazuri Integration API")
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.admin_user, args.admin_password, {})
    if not uid:
        raise SystemExit("Admin authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")
    user_ids = models.execute_kw(
        args.db, uid, args.admin_password,
        "res.users", "search", [[["login", "=", args.api_login]]], {"limit": 1},
    )
    api_password = secrets.token_urlsafe(16)
    if user_ids:
        user_id = user_ids[0]
        models.execute_kw(args.db, uid, args.admin_password, "res.users", "write", [[user_id], {
            "name": args.api_name,
            "password": api_password,
            "groups_id": [(6, 0, [])],
        }])
    else:
        user_id = models.execute_kw(args.db, uid, args.admin_password, "res.users", "create", [{
            "name": args.api_name,
            "login": args.api_login,
            "password": api_password,
        }])

    # Grant Inventory + Sales user groups (approximate for CE)
    group_xmlids = [
        "stock.group_stock_user",
        "sales_team.group_sale_salesman",
        "base.group_user",
    ]
    group_ids = []
    for xmlid in group_xmlids:
        found = models.execute_kw(
            args.db, uid, args.admin_password,
            "ir.model.data", "search_read",
            [[["module", "=", xmlid.split(".")[0]], ["name", "=", xmlid.split(".")[1]]]],
            {"fields": ["res_id"], "limit": 1},
        )
        if found:
            group_ids.append(found[0]["res_id"])
    if group_ids:
        models.execute_kw(args.db, uid, args.admin_password, "res.users", "write", [[user_id], {
            "groups_id": [(6, 0, group_ids)],
        }])

    consumer_key = secrets.token_hex(16)
    consumer_secret = secrets.token_hex(32)

    print("=== Nango odoo-cc credentials ===")
    print(f"Domain: {args.url.replace('https://', '').replace('http://', '').split('/')[0]}")
    print(f"Consumer Key: {consumer_key}")
    print(f"Consumer Secret: {consumer_secret}")
    print("")
    print("Register OAuth app manually in Odoo UI:")
    print(f"  Settings → Users → {args.api_name} → OAuth applications → Register")
    print("  (Odoo 18 generates keys in UI — paste into Nango Connect)")
    print("")
    print(f"API user login: {args.api_login}")
    print(f"API user password: {api_password}")


if __name__ == "__main__":
    main()
