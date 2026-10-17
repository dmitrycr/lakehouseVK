#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
compose=(
  docker compose
  -f docker-compose.yml
  -f docker-compose.superset.yml
)

"${compose[@]}" up -d --build superset
"${compose[@]}" exec -T superset superset db upgrade
# create-admin exits harmlessly if this local account already exists.
"${compose[@]}" exec -T superset sh -c '
  superset fab create-admin \
    --username admin \
    --firstname Lab \
    --lastname Student \
    --email admin@localhost \
    --password "$SUPERSET_ADMIN_PASSWORD"
'
"${compose[@]}" exec -T superset superset init
"${compose[@]}" exec -T superset python - < scripts/superset_setup.py
