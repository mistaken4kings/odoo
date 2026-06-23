#!/usr/bin/env python3
"""Seed Sam West sample products into Odoo via XML-RPC."""
from __future__ import annotations

import argparse
import json
import os
import xmlrpc.client

SAMPLE_PRODUCTS = [
    {"code": "SW-001", "name": "ABABIL PARBOILED RICE 10KG", "brand": "Ababil", "price": 1295, "category": "grains", "uom": "BAG"},
    {"code": "SW-002", "name": "AL-MAHAL BIRYANI RICE 10KG", "brand": "Al-mahal", "price": 1030, "category": "grains", "uom": "BAG"},
    {"code": "SW-003", "name": "CROWN BASMATI RICE 10KG", "brand": "Crown", "price": 1235, "category": "grains", "uom": "BAG"},
    {"code": "SW-004", "name": "FALCON BIRYANI RICE 10KG", "brand": "Falcon", "price": 1070, "category": "grains", "uom": "BAG"},
    {"code": "SW-005", "name": "FZAMI LONG GRAIN RICE 10KG", "brand": "Fzami", "price": 2150, "category": "grains", "uom": "BAG"},
    {"code": "SW-006", "name": "FZAMI BIRYANI RICE 10KG", "brand": "Fzami", "price": 1100, "category": "grains", "uom": "BAG"},
    {"code": "SW-007", "name": "KENYA GOLD MAIZE MEAL 2KG", "brand": "Kenya Gold", "price": 180, "category": "grains", "uom": "BAG"},
    {"code": "SW-008", "name": "JOGOO MAIZE MEAL 2KG", "brand": "Jogoo", "price": 175, "category": "grains", "uom": "BAG"},
    {"code": "SW-009", "name": "EXE ALL PURPOSE FLOUR 2KG", "brand": "Exe", "price": 220, "category": "grains", "uom": "BAG"},
    {"code": "SW-010", "name": "KENBLEACH JIK 5L", "brand": "Kenbleach", "price": 650, "category": "household", "uom": "JERRYCAN"},
    {"code": "SW-011", "name": "SUNLIGHT DISHWASHING 750ML", "brand": "Sunlight", "price": 195, "category": "household", "uom": "BOTTLE"},
    {"code": "SW-012", "name": "OMO HANDWASHING POWDER 2KG", "brand": "Omo", "price": 520, "category": "household", "uom": "BAG"},
    {"code": "SW-013", "name": "CLOSE UP TOOTHPASTE 140G", "brand": "Close Up", "price": 165, "category": "personal care", "uom": "TUBE"},
    {"code": "SW-014", "name": "COLGATE MAX FRESH 140G", "brand": "Colgate", "price": 175, "category": "personal care", "uom": "TUBE"},
    {"code": "SW-015", "name": "COCA COLA 500ML", "brand": "Coca Cola", "price": 75, "category": "beverages", "uom": "BOTTLE"},
    {"code": "SW-016", "name": "KERINGET WATER 500ML", "brand": "Keringet", "price": 55, "category": "beverages", "uom": "BOTTLE"},
    {"code": "SW-017", "name": "BIDCO COOKING OIL 5L", "brand": "Bidco", "price": 1450, "category": "oils", "uom": "JERRYCAN"},
    {"code": "SW-018", "name": "KASARANI VEGETABLE OIL 5L", "brand": "Kasarani", "price": 1380, "category": "oils", "uom": "JERRYCAN"},
    {"code": "SW-019", "name": "BLUE BAND MARGARINE 1KG", "brand": "Blue Band", "price": 420, "category": "dairy", "uom": "TUB"},
    {"code": "SW-020", "name": "BROOKSIDE MILK 500ML", "brand": "Brookside", "price": 65, "category": "dairy", "uom": "BOTTLE"},
]


def load_products(path: str | None) -> list[dict]:
    if not path:
        return SAMPLE_PRODUCTS
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        rows = data
    else:
        rows = data.get("products") or []
    out = []
    for row in rows:
        if row.get("distributorName") and row.get("distributorName") != "Sam West":
            continue
        out.append({
            "code": row.get("code") or row.get("itemCode") or "",
            "name": row.get("name") or row.get("itemDescription") or "",
            "brand": row.get("brand") or "",
            "price": float(row.get("price") or row.get("unitPrice") or 0),
            "category": row.get("category") or "general",
            "uom": row.get("unit") or row.get("uom") or "Units",
        })
        if len(out) >= 100:
            break
    return out or SAMPLE_PRODUCTS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")
    categ_id = models.execute_kw(
        args.db, uid, args.password,
        "product.category", "search", [[["name", "=", "Sam West Catalog"]]], {"limit": 1},
    )
    if not categ_id:
        categ_id = [models.execute_kw(
            args.db, uid, args.password,
            "product.category", "create", [{"name": "Sam West Catalog"}],
        )]

    created = 0
    updated = 0
    for product in load_products(args.json_path):
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
            "sale_ok": True,
            "purchase_ok": True,
            "description_sale": f"{product['brand']} — Sam West pricelist sample",
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

    print(json.dumps({"created": created, "updated": updated, "total": created + updated}))


if __name__ == "__main__":
    main()
