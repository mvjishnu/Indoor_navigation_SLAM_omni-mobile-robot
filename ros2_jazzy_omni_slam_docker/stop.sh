#!/usr/bin/env bash
# Stop and remove the container (image, workspace build and history are kept).
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"
if docker compose version >/dev/null 2>&1; then docker compose down; else docker-compose down; fi
