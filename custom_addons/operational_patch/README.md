# Odoo operational.patch module

Scaffold for `timothylidede/odoo` branch `18.0`.

## Install on demo Odoo (35.202.115.233)

```bash
rsync -av scripts/odoo-operational-patch/ ubuntu@35.202.115.233:/opt/odoo/addons/operational_patch/
# Restart Odoo and install "Mazuri Operational Patch" from Apps
```

The FastAPI backend syncs merged `staging_proposals` via
`services/operational_patch_odoo_service.py` after merge.
