#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
if [[ ! -f .env ]]; then
  echo "Missing .env: run cp .env.example .env" >&2
  exit 1
fi
set -a
source .env
set +a

printf 'Bootstrapping Lakekeeper (409 means already bootstrapped)...\n'
bootstrap_code=$(curl -sS -o /tmp/vk-lakehouse-bootstrap-response -w '%{http_code}' \
  -X POST http://localhost:8181/management/v1/bootstrap \
  -H 'Content-Type: application/json' \
  -d '{"accept-terms-of-use":true}')
if [[ "$bootstrap_code" != "200" && "$bootstrap_code" != "201" && "$bootstrap_code" != "204" && "$bootstrap_code" != "409" ]]; then
  cat /tmp/vk-lakehouse-bootstrap-response >&2
  printf '\nBootstrap HTTP %s\n' "$bootstrap_code" >&2
  exit 1
fi

printf 'Creating warehouse lab...\n'
warehouse_payload=$(cat <<JSON
{
  "warehouse-name": "lab",
  "project-id": "00000000-0000-0000-0000-000000000000",
  "storage-profile": {
    "type": "s3",
    "bucket": "lakehouse",
    "key-prefix": "warehouse",
    "region": "local-01",
    "endpoint": "http://minio:9000",
    "path-style-access": true,
    "flavor": "s3-compat",
    "sts-enabled": false,
    "remote-signing-enabled": true
  },
  "storage-credential": {
    "type": "s3",
    "credential-type": "access-key",
    "access-key-id": "$MINIO_ROOT_USER",
    "secret-access-key": "$MINIO_ROOT_PASSWORD"
  }
}
JSON
)
warehouse_code=$(curl -sS -o /tmp/vk-lakehouse-warehouse-response -w '%{http_code}' \
  -X POST http://localhost:8181/management/v1/warehouse \
  -H 'Content-Type: application/json' \
  --data-binary "$warehouse_payload")
if [[ "$warehouse_code" == "200" || "$warehouse_code" == "201" || "$warehouse_code" == "204" ]]; then
  echo 'Warehouse lab created.'
elif [[ "$warehouse_code" == "409" ]]; then
  echo 'Warehouse lab already exists.'
else
  cat /tmp/vk-lakehouse-warehouse-response >&2
  printf '\nWarehouse HTTP %s\n' "$warehouse_code" >&2
  exit 1
fi

echo 'Check: docker compose exec trino trino --execute "SHOW SCHEMAS FROM lakehouse"'
