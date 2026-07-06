# Mazuri Connector

Installable Odoo app for one-click Mazuri integration (GitHub App-style connect).

## Install

1. Mount `custom_addons` in Odoo (see `deploy/docker-compose.yml`)
2. Update apps list in Odoo → Apps → search **Mazuri Connector** → Install
3. Set `ODOO_MAZURI_CLIENT_SECRET` in deploy `.env` (must match `MAZURI_ODOO_CLIENT_SECRET` on Vercel)

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
