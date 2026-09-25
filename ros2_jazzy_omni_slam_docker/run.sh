#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

# ============================================================
# Host user information
# ============================================================

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

# ============================================================
# Container user
# ============================================================

export CONTAINER_USER="omni_robot"

# ============================================================
# Host device groups
# ============================================================

export DIALOUT_GID="$(getent group dialout | cut -d: -f3 || echo 20)"
export VIDEO_GID="$(getent group video | cut -d: -f3 || echo 44)"

# ============================================================
# X11 authentication
# ============================================================

export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Allow local X11 clients
xhost +local:docker >/dev/null 2>&1 || true

# ============================================================
# Start container
# ============================================================

docker compose up -d

# ============================================================
# Open interactive shell
# ============================================================

exec docker compose exec ros2 bash