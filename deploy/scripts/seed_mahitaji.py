#!/usr/bin/env python3
"""Seed Mahitaji Enterprises catalog into Odoo from the pricelist PDF."""
from __future__ import annotations

import argparse
import json
import os
import re
import xmlrpc.client

try:
    import pdfplumber
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install pdfplumber: pip install pdfplumber") from exc

COMPANY_NAME = "Mahitaji Enterprises Ltd"
CATALOG_CATEGORY = "Mahitaji Catalog"
DEFAULT_PDF = os.path.join(
    os.path.dirname(__file__),
    "../../../../mazuri/app/brands/assets/docs/mahitaji pricelist.pdf",
)


def normalize_price(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = re.sub(r"[KES|KSH|KSHS|,]", "", str(value).upper()).strip()
    match = re.search(r"[\d.]+", cleaned)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def parse_mahitaji_pdf(path: str, limit: int | None = None) -> list[dict]:
    products: list[dict] = []
    seen: set[tuple[str, str]] = set()

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    code = str(row[0] or "").strip()
                    name = str(row[1] or "").strip()
                    unit = str(row[2] or "").strip() or "Units"
                    price = normalize_price(str(row[3] or ""))
                    if not code or not name or price is None:
                        continue
                    upper = code.upper()
                    if (
                        upper in {"CODE", "ITEM"}
                        or "MAHITAJI" in upper
                        or upper == "PRICE LIST"
                        or code.startswith("[")
                    ):
                        continue
                    key = (code, unit)
                    if key in seen:
                        continue
                    seen.add(key)
                    sku = f"{code}-{unit}" if unit else code
                    products.append({
                        "code": sku,
                        "name": name,
                        "unit": unit,
                        "price": price,
                        "brand": "Mahitaji",
                        "category": "general",
                        "description": f"{name} ({unit}) — Mahitaji pricelist",
                    })
                    if limit and len(products) >= limit:
                        return products
    return products


def wipe_active_products(models, db: str, uid: int, password: str) -> int:
    product_ids = models.execute_kw(
        db, uid, password,
        "product.product", "search", [[["active", "=", True]]],
    )
    if not product_ids:
        return 0
    models.execute_kw(
        db, uid, password,
        "product.product", "write",
        [product_ids, {"active": False, "sale_ok": False, "purchase_ok": False}],
    )
    return len(product_ids)


def ensure_company(models, db: str, uid: int, password: str) -> int:
    companies = models.execute_kw(
        db, uid, password,
        "res.company", "search_read", [[]],
        {"fields": ["id", "name"], "limit": 5},
    )
    company_id = int(companies[0]["id"]) if companies else None
    if not company_id:
        company_id = int(models.execute_kw(
            db, uid, password,
            "res.company", "create", [{"name": COMPANY_NAME}],
        ))
    else:
        models.execute_kw(
            db, uid, password,
            "res.company", "write", [[company_id], {"name": COMPANY_NAME}],
        )
    return company_id


def ensure_kes_currency(models, db: str, uid: int, password: str, company_id: int) -> None:
    currency_ids = models.execute_kw(
        db, uid, password,
        "res.currency", "search", [[["name", "=", "KES"]]],
        {"limit": 1, "context": {"active_test": False}},
    )
    if not currency_ids:
        currency_ids = models.execute_kw(
            db, uid, password,
            "res.currency", "search", [[["name", "ilike", "KES"]]],
            {"limit": 1, "context": {"active_test": False}},
        )
    if not currency_ids:
        currency_ids = [models.execute_kw(
            db, uid, password,
            "res.currency", "create", [{
                "name": "KES",
                "symbol": "KSh",
                "rounding": 0.01,
                "active": True,
            }],
        )]
    else:
        models.execute_kw(
            db, uid, password,
            "res.currency", "write",
            [currency_ids, {"active": True}],
        )
    models.execute_kw(
        db, uid, password,
        "res.company", "write",
        [[company_id], {"currency_id": currency_ids[0]}],
    )


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
        "description_sale": product["description"],
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
    parser = argparse.ArgumentParser(description="Seed Mahitaji catalog into Odoo from PDF")
    parser.add_argument("--url", default=os.environ.get("ODOO_URL", "http://127.0.0.1:8069"))
    parser.add_argument("--db", default=os.environ.get("ODOO_DB", "mazuri"))
    parser.add_argument("--user", default=os.environ.get("ODOO_USER", "admin"))
    parser.add_argument("--password", default=os.environ.get("ODOO_PASSWORD", "admin"))
    parser.add_argument("--pdf", default=os.environ.get("MAHITAJI_PDF", DEFAULT_PDF))
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-wipe", action="store_true", help="Do not archive existing active products")
    args = parser.parse_args()

    products = parse_mahitaji_pdf(args.pdf, args.limit)
    if not products:
        raise SystemExit(f"No products parsed from {args.pdf}")

    common = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/common")
    uid = common.authenticate(args.db, args.user, args.password, {})
    if not uid:
        raise SystemExit("Odoo authentication failed")

    models = xmlrpc.client.ServerProxy(f"{args.url}/xmlrpc/2/object")
    archived = 0 if args.no_wipe else wipe_active_products(models, args.db, uid, args.password)
    company_id = ensure_company(models, args.db, uid, args.password)
    ensure_kes_currency(models, args.db, uid, args.password, company_id)
    categ_id = ensure_category(models, args.db, uid, args.password)

    created = updated = 0
    for index, product in enumerate(products, start=1):
        result = upsert_product(models, args.db, uid, args.password, product, categ_id, company_id)
        if result == "created":
            created += 1
        else:
            updated += 1
        if index % 100 == 0:
            print(f"progress {index}/{len(products)} created={created} updated={updated}", flush=True)

    company = models.execute_kw(
        args.db, uid, args.password,
        "res.company", "read", [[company_id]], {"fields": ["name", "currency_id"]},
    )[0]
    print(json.dumps({
        "company": company,
        "created": created,
        "updated": updated,
        "archived": archived,
        "total": created + updated,
        "source": args.pdf,
    }))


if __name__ == "__main__":
    main()
