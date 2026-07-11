#!/usr/bin/env python3
"""Seed Mahitaji Enterprises catalog into Odoo via XML-RPC.

Creates or renames the default company to Mahitaji Enterprises Ltd and loads
products from the Mazuri pricelist JSON (products.json).
"""
from __future__ import annotations

import argparse
import json
import os
import xmlrpc.client

DEFAULT_JSON = os.path.join(
    os.path.dirname(__file__),
    "../../../../mazuri/app/retailers/backend/products.json",
)
COMPANY_NAME = "Mahitaji Enterprises Ltd"
CATALOG_CATEGORY = "Mahitaji Catalog"


def load_mahitaji_products(path: str, limit: int | None = None, all_products: bool = False) -> list[dict]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    rows = data if isinstance(data, list) else data.get("products") or []
    out: list[dict] = []
    for row in rows:
        if not all_products and row.get("distributorName") and row.get("distributorName") != "Mahitaji":
            continue
        code = str(row.get("code") or row.get("itemCode") or "").strip()
        name = str(row.get("name") or row.get("itemDescription") or "").strip()
        if not code or not name:
            continue
        out.append({
            "code": code,
            "name": name,
            "brand": str(row.get("brand") or "").strip(),
            "price": float(row.get("price") or row.get("unitPrice") or 0),
            "category": str(row.get("category") or "general").strip(),
            "uom": str(row.get("unit") or row.get("uom") or "Units").strip(),
            "description": str(row.get("description") or "").strip(),
        })
        if limit and len(out) >= limit:
            break
    return out


def archive_demo_products(models, db: str, uid: int, password: str) -> int:
    demo_ids = models.execute_kw(
        db, uid, password,
        "product.product", "search",
        [[["default_code", "=like", "SW-%"]]],
    )
    demo_ids += models.execute_kw(
        db, uid, password,
        "product.product", "search",
        [[["default_code", "=like", "BS-%"]]],
    )
    if not demo_ids:
        return 0
    models.execute_kw(
        db, uid, password,
        "product.product", "write",
        [demo_ids, {"active": False, "sale_ok": False, "purchase_ok": False}],
    )
    return len(demo_ids)


def ensure_company(models, db: str, uid: int, password: str, create_new: bool) -> int:
    companies = models.execute_kw(
        db, uid, password,
        "res.company", "search_read", [[]],
        {"fields": ["id", "name"], "limit": 20},
    )
    for company in companies:
        if company.get("name") == COMPANY_NAME:
            return int(company["id"])

    if create_new:
        country_ids = models.execute_kw(
            db, uid, password,
            "res.country", "search", [[["code", "=", "KE"]]], {"limit": 1},
        )
        currency_ids = models.execute_kw(
            db, uid, password,
            "res.currency", "search", [[["name", "=", "KES"]]], {"limit": 1},
        )
        if not currency_ids:
            currency_ids = models.execute_kw(
                db, uid, password,
                "res.currency", "search", [[["name", "=", "USD"]]], {"limit": 1},
            )
        vals = {"name": COMPANY_NAME}
        if country_ids:
            vals["country_id"] = country_ids[0]
        if currency_ids:
            vals["currency_id"] = currency_ids[0]
        return int(models.execute_kw(db, uid, password, "res.company", "create", [vals]))

    if companies:
        models.execute_kw(
            db, uid, password,
            "res.company", "write",
            [[companies[0]["id"]], {"name": COMPANY_NAME}],
        )
        return int(companies[0]["id"])

    return int(models.execute_kw(
        db, uid, password,
        "res.company", "create", [{"name": COMPANY_NAME}],
    ))


def ensure_category(models, db: str, uid: int, password: str) -> int:
    categ_id = models.execute_kw(
        db, uid, password,
        "product.category", "search", [[["name", "=", CATALOG_CATEGORY]]], {"limit": 1},
    )
    if categ_id:
        return int(categ_id[0])
    return int(models.execute_kw(
        db, uid, password,
        "product.category", "create", [{"name": CATALOG_CATEGORY}],
    ))


def upsert_product(
    models,
    db: str,
    uid: int,
    password: str,
    product: dict,
    categ_id: int,
    company_id: int,
) -> str:
    code = product["code"]
    existing = models.execute_kw(
        db, uid, password,
        "product.product", "search", [[["default_code", "=", code]]], {"limit": 1},
    )
    brand = product.get("brand") or "Mahitaji"
    desc = product.get("description") or f"{brand} — {product['name']}"
    vals = {
        "name": product["name"],
        "default_code": code,
        "list_price": product["price"],
        "categ_id": categ_id,
        "company_id": company_id,
        "type": "consu",
        "is_storable": True,
        "sale_ok": True,
        "purchase_ok": True,
        "active": True,
        "description_sale": desc,
    }
    if existing:
        models.execute_kw(db, uid, password, "product.product", "write", [existing, vals])
        return "updated"
    template_id = models.execute_kw(db, uid, password, "product.template", "create", [vals])
    models.execute_kw(
        db, uid, password,
        "product.product", "search", [[["product_tmpl_id", "=", template_id]]], {"limit": 1},
    )
    return "created"


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Mahitaji catalog into Odoo")
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--json", dest="json_path", default=os.environ.get("MAHITAJI_JSON", DEFAULT_JSON))
    parser.add_argument("--limit", type=int, default=None, help="Max products to seed (default: all)")
    parser.add_argument("--all-products", action="store_true", help="Seed every row in JSON (full pricelist)")
    parser.add_argument("--create-company", action="store_true", help="Create a new res.company instead of renaming default")
    parser.add_argument("--keep-demo", action="store_true", help="Do not archive SW-/BS- demo products")
    args = parser.parse_args()

    products = load_mahitaji_products(args.json_path, args.limit, args.all_products)
    if not products:
        raise SystemExit(f"No Mahitaji products found in {args.json_path}")

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")
    archived = 0 if args.keep_demo else archive_demo_products(models, args.db, uid, args.password)
    company_id = ensure_company(models, args.db, uid, args.password, args.create_company)
    categ_id = ensure_category(models, args.db, uid, args.password)

    created = updated = 0
    for index, product in enumerate(products, start=1):
        result = upsert_product(models, args.db, uid, args.password, product, categ_id, company_id)
        if result == "created":
            created += 1
        else:
            updated += 1
        if index % 200 == 0:
            print(f"progress {index}/{len(products)} created={created} updated={updated}", flush=True)

    print(json.dumps({
        "company_id": company_id,
        "company_name": COMPANY_NAME,
        "created": created,
        "updated": updated,
        "archived_demo": archived,
        "total": created + updated,
        "source": args.json_path,
    }))


if __name__ == "__main__":
    main()
