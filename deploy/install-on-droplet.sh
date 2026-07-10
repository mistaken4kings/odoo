#!/usr/bin/env bash
# Bootstrap Odoo 18 on Ubuntu (DigitalOcean mazuri-odoo droplet).
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/mazuri-odoo}"
REPO_URL="${REPO_URL:-https://github.com/timothylidede/odoo.git}"
BRANCH="${BRANCH:-18.0}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq docker.io docker-compose-v2 git curl

systemctl enable docker
systemctl start docker

mkdir -p "$DEPLOY_DIR"
if [[ ! -d "$DEPLOY_DIR/deploy" ]]; then
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$DEPLOY_DIR/src" || {
    mkdir -p "$DEPLOY_DIR/deploy"
  }
  if [[ -d "$DEPLOY_DIR/src/deploy" ]]; then
    cp -a "$DEPLOY_DIR/src/deploy/." "$DEPLOY_DIR/deploy/"
  fi
fi

cd "$DEPLOY_DIR/deploy"

if [[ ! -f .env ]]; then
  ODOO_DB_PASSWORD="$(openssl rand -hex 16)"
  ODOO_ADMIN_PASSWORD="$(openssl rand -hex 12)"
  cat > .env <<EOF
ODOO_DB_PASSWORD=${ODOO_DB_PASSWORD}
ODOO_ADMIN_PASSWORD=${ODOO_ADMIN_PASSWORD}
EOF
  chmod 600 .env
  echo "Wrote credentials to $DEPLOY_DIR/deploy/.env"
fi

# Substitute env into odoo.conf for container
set -a
# shellcheck disable=SC1091
source .env
set +a
envsubst < config/odoo.conf.template > config/odoo.conf 2>/dev/null || cp config/odoo.conf config/odoo.conf

docker compose pull
docker compose up -d

echo "Waiting for Odoo HTTP..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:8069/web/database/selector" >/dev/null; then
    echo "Odoo is up on :8069"
    break
  fi
  sleep 5
done

echo "Bootstrapping database (stock + sale_management + mazuri)..."
docker compose exec -T odoo python3 /mnt/scripts/bootstrap_database.py || {
  echo "Bootstrap script failed — create database 'mazuri' manually if needed."
}

PUBLIC_IP="$(curl -sf ifconfig.me || hostname -I | awk '{print $1}')"
echo ""
echo "=== Mazuri Odoo ==="
echo "URL: http://${PUBLIC_IP}:8069"
echo "Database: mazuri"
echo "Admin password: see ${DEPLOY_DIR}/deploy/.env (ODOO_ADMIN_PASSWORD)"
echo "Modules: stock, sale_management, mazuri (legacy mazuri_connector removed if present)"
echo "Optional: docker compose exec odoo python3 /mnt/scripts/seed_sam_west.py"
