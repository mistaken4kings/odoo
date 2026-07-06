#!/usr/bin/env python3
"""Seed Brookside demo products into Odoo via XML-RPC (replaces Sam West catalog)."""
from __future__ import annotations

import argparse
import json
import os
import xmlrpc.client

BROOKSIDE_PRODUCTS = [
  {"code": "BS-001", "name": "FRESH WHOLE MILK 500ML", "brand": "Brookside", "price": 55, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-002", "name": "FRESH WHOLE MILK 1L", "brand": "Brookside", "price": 95, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-003", "name": "FRESH WHOLE MILK 2L", "brand": "Brookside", "price": 175, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-004", "name": "LONG LIFE WHOLE MILK 200ML", "brand": "Brookside", "price": 35, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-005", "name": "LONG LIFE WHOLE MILK 250ML", "brand": "Brookside", "price": 40, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-006", "name": "LONG LIFE WHOLE MILK 500ML", "brand": "Brookside", "price": 65, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-007", "name": "LONG LIFE WHOLE MILK 1L", "brand": "Brookside", "price": 115, "category": "dairy", "uom": "BOTTLE"},
  {"code": "BS-008", "name": "FULL CREAM MILK POWDER 15G SACHET", "brand": "Brookside", "price": 15, "category": "dairy", "uom": "SACHET"},
  {"code": "BS-009", "name": "FULL CREAM MILK POWDER 250G POUCH", "brand": "Brookside", "price": 285, "category": "dairy", "uom": "POUCH"},
  {"code": "BS-010", "name": "FULL CREAM MILK POWDER 450G POUCH", "brand": "Brookside", "price": 495, "category": "dairy", "uom": "POUCH"},
  {"code": "BS-011", "name": "FULL CREAM MILK POWDER 250G CAN", "brand": "Brookside", "price": 310, "category": "dairy", "uom": "CAN"},
  {"code": "BS-012", "name": "FULL CREAM MILK POWDER 450G CAN", "brand": "Brookside", "price": 520, "category": "dairy", "uom": "CAN"},
  {"code": "BS-013", "name": "FULL CREAM MILK POWDER 900G CAN", "brand": "Brookside", "price": 890, "category": "dairy", "uom": "CAN"},
  {"code": "BS-014", "name": "FULL CREAM MILK POWDER 2500G CAN", "brand": "Brookside", "price": 2100, "category": "dairy", "uom": "CAN"},
  {"code": "BS-015", "name": "BUTTER 8G", "brand": "Brookside", "price": 8, "category": "dairy", "uom": "PACK"},
  {"code": "BS-016", "name": "BUTTER 250G", "brand": "Brookside", "price": 320, "category": "dairy", "uom": "TUB"},
  {"code": "BS-017", "name": "BUTTER 500G", "brand": "Brookside", "price": 580, "category": "dairy", "uom": "TUB"},
]


def archive_sam_west_products(models, db: str, uid: int, password: str) -> int:
    sw_ids = models.execute_kw(
        db, uid, password,
        "product.product", "search", [[["default_code", "=like", "SW-%"]]],
    )
    if not sw_ids:
        return 0
    models.execute_kw(
        db, uid, password,
        "product.product", "write",
        [sw_ids, {"active": False, "sale_ok": False, "purchase_ok": False}],
    )
    return len(sw_ids)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--keep-sam-west", action="store_true", help="Do not archive SW-* products")
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")
    archived = 0
    if not args.keep_sam_west:
        archived = archive_sam_west_products(models, args.db, uid, args.password)

    categ_id = models.execute_kw(
        args.db, uid, args.password,
        "product.category", "search", [[["name", "=", "Brookside Catalog"]]], {"limit": 1},
    )
    if not categ_id:
        categ_id = [models.execute_kw(
            args.db, uid, args.password,
            "product.category", "create", [{"name": "Brookside Catalog"}],
        )]

    created = 0
    updated = 0
    for product in BROOKSIDE_PRODUCTS:
        code = product["code"]
        existing = models.execute_kw(
            args.db, uid, args.password,
            "product.product", "search", [[["default_code", "=", code]]], {"limit": 1},
        )
        vals = {
            "name": product["name"],
            "default_code": code,
            "list_price": product["price"],
            "categ_id": categ_id[0],
            "type": "consu",
            "is_storable": True,
            "sale_ok": True,
            "purchase_ok": True,
            "active": True,
            "description_sale": f"{product['brand']} Farm Fresh — {product['name']}",
        }
        if existing:
            models.execute_kw(args.db, uid, args.password, "product.product", "write", [existing, vals])
            updated += 1
        else:
            template_id = models.execute_kw(args.db, uid, args.password, "product.template", "create", [vals])
            models.execute_kw(
                args.db, uid, args.password,
                "product.product", "search", [[["product_tmpl_id", "=", template_id]]], {"limit": 1},
            )
            created += 1

    print(json.dumps({
        "created": created,
        "updated": updated,
        "archived_sam_west": archived,
        "total": created + updated,
    }))


if __name__ == "__main__":
    main()
