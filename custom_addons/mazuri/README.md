# Mazuri (Odoo app)

Single Odoo app centralizing every Mazuri capability:

| Capability | Where it lives |
|------------|----------------|
| One-click connect (OAuth-style authorize) | `controllers/main.py`, `views/mazuri_connect_templates.xml` |
| Connection registry | `models/mazuri_connection.py` (Mazuri → Connections menu) |
| Auth codes (single-use token exchange) | `models/mazuri_auth_code.py` |
| Financing ledger (Pay in 30) | `models/mazuri_financing.py` (Mazuri → Financing menu) |
| "Mazuri Pay in 30 (interest free)" payment term | created by `hooks.py` on install |
| App Store listing assets | `static/description/icon.png`, `static/description/index.html` |

Catalog/inventory sync and order push are performed by the Mazuri platform
through the connected API user over XML-RPC — this module provides the
authorization surface and the in-Odoo visibility (connections + financing).

## Install (self-hosted / droplet)

1. Mount `custom_addons` in Odoo (see `deploy/docker-compose.yml`)
2. Update apps list in Odoo → Apps → search **Mazuri** → Install
3. Set `ODOO_MAZURI_CLIENT_SECRET` in deploy `.env` (must match `MAZURI_ODOO_CLIENT_SECRET` on Vercel)

> Upgrading from the old `mazuri_connector` module: install `mazuri`, then
> uninstall `mazuri_connector`. Routes and models are identical
> (`mazuri.connection`, `mazuri.auth.code`, `/mazuri/*`), so reconnects are
> not required, but the module technical name changed.

## Connect flow

1. User clicks **Connect Odoo** in Mazuri and enters their Odoo URL
2. Mazuri redirects to `{odoo_url}/mazuri/connect?...`
3. Odoo admin authorizes
4. Mazuri receives callback, exchanges code at `/mazuri/oauth/token`
5. Products sync via direct XML-RPC (no manual OAuth keys)

## Endpoints

| Route | Purpose |
|-------|---------|
| `POST /mazuri/status` | Check module installed |
| `GET /mazuri/connect` | Authorization screen |
| `POST /mazuri/connect/approve` | Approve and redirect with code |
| `POST /mazuri/oauth/token` | Exchange code for API credentials |

Client ID is always `mazuri-app`.

## Financing (`mazuri.financing`)

Mazuri writes financed-order records over the connected API user:

```python
models.execute_kw(db, uid, password, 'mazuri.financing', 'create', [{
    'name': 'MZR-48213',
    'org_id': 'org_brookside',
    'retailer_name': 'Kamau General Store',
    'principal': 38480,
    'payout_speed': 'net_30',
    'payout_total': 38480,
    'due_date': '2026-08-08',
    'state': 'disbursed',
}])
```

States: `pending → accepted → disbursed → repaid` (or `overdue` / `declined`).

## Publishing to the Odoo App Store

The App Store indexes a Git repo whose **branch name is the Odoo version** and
whose **root contains the module folder**. This repo is a fork of `odoo/odoo`,
so it cannot be submitted directly. To publish:

1. Create a dedicated repo (e.g. `mazuri-odoo-apps`), private is fine
2. Create branch `18.0`; copy `custom_addons/mazuri/` → `mazuri/` at repo root
3. Invite the GitHub user **`online-odoo`** as a read collaborator
4. Submit at https://apps.odoo.com/apps/upload with
   `ssh://git@github.com/<org>/mazuri-odoo-apps#18.0`
5. Every push to `18.0` re-triggers the store scan automatically
