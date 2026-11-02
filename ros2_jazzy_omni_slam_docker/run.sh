#!/usr/bin/env bash

set -euo pipefail

cd "$(dirname "$0")"

# ============================================================
# Host user information
# ============================================================

export HOST_UID="$(id -u)"
export HOST_GID="$(id -g)"

export DISPLAY="${DISPLAY:-}"
export WAYLAND_DISPLAY_CONTAINER="wayland-0"
export WAYLAND_SOCKET_PATH="/dev/null"
if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    if [[ "$WAYLAND_DISPLAY" = /* ]]; then
        HOST_WAYLAND_SOCKET="$WAYLAND_DISPLAY"
        export WAYLAND_DISPLAY_CONTAINER="$(basename "$HOST_WAYLAND_SOCKET")"
    else
        HOST_WAYLAND_SOCKET="${XDG_RUNTIME_DIR:-/run/user/$HOST_UID}/$WAYLAND_DISPLAY"
        export WAYLAND_DISPLAY_CONTAINER="$WAYLAND_DISPLAY"
    fi
    if [[ -S "$HOST_WAYLAND_SOCKET" ]]; then
        export WAYLAND_SOCKET_PATH="$HOST_WAYLAND_SOCKET"
    else
        echo "Ignoring unavailable Wayland socket: $HOST_WAYLAND_SOCKET" >&2
        export WAYLAND_DISPLAY_CONTAINER="wayland-0"
    fi
fi

if [[ -n "$DISPLAY" ]]; then
    X11_DISPLAY="${DISPLAY##*:}"
    X11_DISPLAY="${X11_DISPLAY%%.*}"
    if [[ -S "/tmp/.X11-unix/X${X11_DISPLAY}" ]]; then
        xhost "+SI:localuser:$(id -un)" >/dev/null 2>&1 || true
    else
        echo "X11 display socket is unavailable; trying native Wayland." >&2
        export DISPLAY=""
    fi
fi
if [[ -z "$DISPLAY" && "$WAYLAND_SOCKET_PATH" == /dev/null ]]; then
    echo "No usable X11/XWayland or Wayland display was found." >&2
    exit 1
fi

# Pick the active default-route interface for ROS 2 discovery. Keep loopback
# for local nodes, and use Cyclone DDS auto-detection if no route exists.
mkdir -p ../.ros2_ws
ROS_IFACE="$(ip -o route show default 2>/dev/null | awk 'NR == 1 {for (i=1; i<=NF; i++) if ($i == "dev") {print $(i+1); exit}}')"
if [[ "$ROS_IFACE" =~ ^[[:alnum:]_.:-]+$ ]]; then
    cat > ../.ros2_ws/cyclonedds.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config"><Domain Id="any"><General><Interfaces><NetworkInterface name="lo" priority="10" multicast="true"/><NetworkInterface name="$ROS_IFACE" priority="0" multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>
EOF
else
    cat > ../.ros2_ws/cyclonedds.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config"><Domain Id="any"><General><Interfaces><NetworkInterface name="lo" priority="10" multicast="true"/><NetworkInterface autodetermine="true" priority="0" multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>
EOF
fi

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

export XAUTHORITY_PATH="${XAUTHORITY:-$HOME/.Xauthority}"
[[ -r "$XAUTHORITY_PATH" ]] || export XAUTHORITY_PATH=/dev/null
if [[ -d /dev/dri ]]; then
    export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-0}"
else
    export LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-1}"
fi

COMPOSE_ARGS=(-f docker-compose.yml)
if command -v nvidia-smi >/dev/null 2>&1 && docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q '"nvidia"'; then
    COMPOSE_ARGS+=(-f docker-compose.nvidia.yml)
fi

# ============================================================
# Start container
# ============================================================

docker compose "${COMPOSE_ARGS[@]}" up -d

# ============================================================
# Open interactive shell
# ============================================================

exec docker compose "${COMPOSE_ARGS[@]}" exec ros2 bash
