#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Three independent writes of every format/codec combination at LAB_SCALE (default sf1).
# Stops below 22 GiB free; creates unique schemas and retains all data.
python3 scripts/lab.py benchmark
