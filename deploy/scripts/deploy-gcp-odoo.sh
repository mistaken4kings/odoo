#!/usr/bin/env bash
# Deploy Mazuri Odoo custom_addons to GCP vendai-gcp-1.
set -euo pipefail

INSTANCE="${GCP_INSTANCE_NAME:-vendai-gcp-1}"
ZONE="${GCP_ZONE:-us-central1-a}"
PROJECT="${GCP_PROJECT_ID:-spiro-445121}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_DIR="${REMOTE_ODOO_DIR:-/opt/mazuri-odoo}"
DEPLOY_DIR="${REMOTE_DIR}/deploy"
# docker-compose mounts ../custom_addons → /mnt/custom-addons (not deploy/custom_addons)
ADDONS_DST="${REMOTE_DIR}/custom_addons"
SCRIPTS_DST="${DEPLOY_DIR}/scripts"

echo "==> Sync Odoo from ${REPO_ROOT} to ${INSTANCE}"
TAR="/tmp/mazuri-odoo-deploy.tar.gz"
tar czf "$TAR" -C "$REPO_ROOT" custom_addons deploy/scripts

gcloud compute scp --zone="$ZONE" --project="$PROJECT" "$TAR" "${INSTANCE}:/tmp/mazuri-odoo-deploy.tar.gz"
rm -f "$TAR"

gcloud compute ssh "$INSTANCE" --zone="$ZONE" --project="$PROJECT" --command="
set -euo pipefail
sudo mkdir -p /tmp/mazuri-odoo-extract ${ADDONS_DST} ${SCRIPTS_DST}
sudo tar xzf /tmp/mazuri-odoo-deploy.tar.gz -C /tmp/mazuri-odoo-extract
sudo cp -a /tmp/mazuri-odoo-extract/custom_addons/. ${ADDONS_DST}/
sudo cp -a /tmp/mazuri-odoo-extract/deploy/scripts/. ${SCRIPTS_DST}/
sudo rm -rf /tmp/mazuri-odoo-extract /tmp/mazuri-odoo-deploy.tar.gz

cd ${DEPLOY_DIR}
if docker compose ps odoo >/dev/null 2>&1; then
  docker compose restart odoo
  for i in \$(seq 1 36); do
    curl -sf http://127.0.0.1:8069/web/database/selector >/dev/null && break
    sleep 5
  done
  docker compose exec -T odoo python3 /mnt/scripts/upgrade_mazuri_module.py
  docker compose exec -T odoo python3 /mnt/scripts/seed_mahitaji.py --url http://127.0.0.1:8069 || true
else
  echo 'Odoo compose not running at ${DEPLOY_DIR}'
  exit 1
fi
"

echo "==> Odoo deploy complete"
