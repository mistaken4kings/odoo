# Odoo deploy environment

Set the same shared secret on Odoo and Mazuri (Vercel):

```
ODOO_MAZURI_CLIENT_SECRET=your-long-random-secret
```

On Vercel (mazuri brands app):

```
MAZURI_ODOO_CLIENT_SECRET=your-long-random-secret
MAZURI_APP_URL=https://mazuri.app
```

After `docker compose up`, install **Mazuri Connector** from Odoo Apps (or run `bootstrap_database.py`).
