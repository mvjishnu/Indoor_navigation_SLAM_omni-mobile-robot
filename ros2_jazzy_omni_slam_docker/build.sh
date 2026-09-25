#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"
export CONTAINER_USER="omni_robot"
export DIALOUT_GID="$(getent group dialout | cut -d: -f3 || echo 20)"
export VIDEO_GID="$(getent group video | cut -d: -f3 || echo 44)"

echo "Building ROS 2 Jazzy + Gazebo Harmonic image..."
echo "Container user: ${CONTAINER_USER} (${HOST_UID}:${HOST_GID})"

docker compose build \
    --build-arg UID="${HOST_UID}" \
    --build-arg GID="${HOST_GID}" \
    --build-arg USERNAME="${CONTAINER_USER}"