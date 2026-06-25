# Mazuri Odoo test instance

**Host:** GCP `vendai-gcp-1` — `35.202.115.233` (co-located with PocketBase + FastAPI)  
**URL:** http://35.202.115.233:8069

> Previous DO droplet `mazuri-odoo` (`64.23.144.200`) was decommissioned.  
**Database:** `mazuri`

## Login

| Field | Value |
|-------|--------|
| Email | `admin` |
| Password | `admin` |

Master password (database manager) and Postgres password are in `/opt/mazuri-odoo/deploy/.env` on the droplet.

## Modules installed

- Inventory (`stock`)
- Sales (`sale_management`)

## Sample catalog

20 Sam West SKUs seeded (`SW-001` … `SW-020`) — rice, oils, household, beverages.

Re-seed:

```bash
ssh -i ~/.ssh/vendai_do_deploy root@64.23.144.200
cd /opt/mazuri-odoo/deploy
docker compose exec odoo python3 /mnt/scripts/seed_sam_west.py \
  --url http://127.0.0.1:8069 --db mazuri --user admin --password admin
```

## Nango connect (odoo-cc)

1. In Odoo: **Settings → Users → admin → OAuth applications → Register**
2. In Nango Connect use:
   - **Domain:** `64.23.144.200:8069` (or your DNS later)
   - **Consumer Key / Secret** from the OAuth app

## SSH

```bash
ssh -i ~/.ssh/vendai_do_deploy root@64.23.144.200
```

Deploy key for this droplet: `cursor-agent-odoo-3671` (registered on DigitalOcean).
