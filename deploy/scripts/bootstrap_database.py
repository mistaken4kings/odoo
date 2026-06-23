#!/usr/bin/env python3
"""Create mazuri Odoo database with Inventory + Sales modules."""
from __future__ import annotations

import os
import subprocess
import sys
import time
import xmlrpc.client


def wait_for_odoo(url: str, timeout_s: int = 300) -> None:
    import urllib.request

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/web/database/selector", timeout=5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(5)
    raise TimeoutError("Odoo did not become ready")


def main() -> None:
    url = os.environ.get("ODOO_URL", "http://127.0.0.1:8069").rstrip("/")
    db = os.environ.get("ODOO_DB", "mazuri")
    admin_password = os.environ.get("ODOO_ADMIN_PASSWORD", "admin")
    master_password = os.environ.get("ODOO_MASTER_PASSWORD", admin_password)

    wait_for_odoo(url)

    db_service = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    existing = db_service.list()
    if db not in existing:
        try:
            db_service.create_database(
                master_password,
                db,
                False,
                "en_US",
                admin_password,
                "admin",
                "admin@mazuri.app",
                "KE",
            )
            print(f"Created database {db}")
        except xmlrpc.client.Fault:
            subprocess.check_call([
                "odoo", "db", "init", db,
                "--master-password", master_password,
                "--username", "admin",
                "--password", admin_password,
                "--country", "KE",
                "--without-demo", "all",
            ])
            print(f"Created database {db} via CLI")
    else:
        print(f"Database {db} already exists")

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, "admin", admin_password, {})
    if not uid:
        raise SystemExit("Could not authenticate admin user")

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    for module in ("stock", "sale_management"):
        state = models.execute_kw(
            db, uid, admin_password,
            "ir.module.module", "search_read",
            [[["name", "=", module]]],
            {"fields": ["state"], "limit": 1},
        )
        if state and state[0]["state"] != "installed":
            models.execute_kw(
                db, uid, admin_password,
                "ir.module.module", "button_immediate_install",
                [[state[0]["id"]]],
            )
            print(f"Installed module {module}")

    seed = "/mnt/scripts/seed_sam_west.py"
    if os.path.exists(seed):
        subprocess.check_call([
            sys.executable, seed,
            "--url", url,
            "--db", db,
            "--user", "admin",
            "--password", admin_password,
        ])


if __name__ == "__main__":
    main()
