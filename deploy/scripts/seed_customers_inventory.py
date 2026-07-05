#!/usr/bin/env python3
"""Seed sample customers and inventory quantities into Odoo via XML-RPC."""
from __future__ import annotations

import argparse
import json
import os
import xmlrpc.client

SAMPLE_CUSTOMERS = [
    {"name": "Nakumatt Westlands", "email": "orders@nakumatt.example", "phone": "+254712000001", "city": "Nairobi"},
    {"name": "Quickmart Kilimani", "email": "buyer@quickmart.example", "phone": "+254712000002", "city": "Nairobi"},
    {"name": "Chandarana Foodplus", "email": "procurement@chandarana.example", "phone": "+254712000003", "city": "Nairobi"},
    {"name": "Naivas Thika Road", "email": "store@naivas.example", "phone": "+254712000004", "city": "Thika"},
    {"name": "Carrefour Two Rivers", "email": "retail@carrefour.example", "phone": "+254712000005", "city": "Nairobi"},
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--qty", type=int, default=120, help="Default on-hand quantity per SKU")
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")

    customers_created = 0
    customers_updated = 0
    for customer in SAMPLE_CUSTOMERS:
        existing = models.execute_kw(
            args.db, uid, args.password,
            "res.partner", "search", [[["name", "=", customer["name"]], ["customer_rank", ">", 0]]],
            {"limit": 1},
        )
        vals = {
            "name": customer["name"],
            "email": customer["email"],
            "phone": customer["phone"],
            "city": customer["city"],
            "country_id": models.execute_kw(
                args.db, uid, args.password,
                "res.country", "search", [[["code", "=", "KE"]]], {"limit": 1},
            )[0],
            "customer_rank": 1,
            "company_type": "company",
        }
        if existing:
            models.execute_kw(args.db, uid, args.password, "res.partner", "write", [existing, vals])
            customers_updated += 1
        else:
            models.execute_kw(args.db, uid, args.password, "res.partner", "create", [vals])
            customers_created += 1

    warehouse_ids = models.execute_kw(
        args.db, uid, args.password,
        "stock.warehouse", "search", [[]], {"limit": 1},
    )
    if not warehouse_ids:
        raise SystemExit("No stock warehouse found — install Inventory module first")
    location_ids = models.execute_kw(
        args.db, uid, args.password,
        "stock.warehouse", "read", [warehouse_ids], {"fields": ["lot_stock_id"]},
    )
    stock_location_id = location_ids[0]["lot_stock_id"][0]

    product_ids = models.execute_kw(
        args.db, uid, args.password,
        "product.product", "search", [[["default_code", "like", "SW-%"]]],
    )
    if product_ids:
        template_ids = models.execute_kw(
            args.db, uid, args.password,
            "product.product", "read", [product_ids], {"fields": ["product_tmpl_id"]},
        )
        tmpl_ids = list({row["product_tmpl_id"][0] for row in template_ids})
        models.execute_kw(
            args.db, uid, args.password,
            "product.template", "write", [tmpl_ids, {"is_storable": True}],
        )

    inventory_updated = 0
    for product_id in product_ids:
        quant_ids = models.execute_kw(
            args.db, uid, args.password,
            "stock.quant", "search", [[["product_id", "=", product_id], ["location_id", "=", stock_location_id]]],
            {"limit": 1},
        )
        vals = {
            "inventory_quantity": args.qty,
            "inventory_quantity_set": True,
        }
        if quant_ids:
            models.execute_kw(args.db, uid, args.password, "stock.quant", "write", [quant_ids, vals])
        else:
            models.execute_kw(
                args.db, uid, args.password,
                "stock.quant", "create", [{
                    "product_id": product_id,
                    "location_id": stock_location_id,
                    **vals,
                }],
            )
        inventory_updated += 1

    print(json.dumps({
        "customers_created": customers_created,
        "customers_updated": customers_updated,
        "inventory_skus": inventory_updated,
        "default_qty": args.qty,
    }))


if __name__ == "__main__":
    main()
