#!/usr/bin/env bash
# One-stop launcher: detects this host, writes .env, builds the image if
# needed, starts the container and opens a shell in it.
#
#   ./run.sh               build if needed, start, open a shell
#   ./run.sh --build       force an image rebuild first (after Dockerfile/packages changes)
#   ./run.sh --build-only  just build the image
#   ./run.sh --no-gpu      do not request the NVIDIA GPU
#   ./run.sh <cmd...>      run a command in the container instead of a shell
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")"

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo ">> $*"; }

FORCE_BUILD=0; BUILD_ONLY=0; USE_GPU=auto; CMD=()
while (($#)); do
    case "$1" in
        --build)      FORCE_BUILD=1 ;;
        --build-only) FORCE_BUILD=1; BUILD_ONLY=1 ;;
        --no-gpu)     USE_GPU=no ;;
        -h|--help)    sed -n '2,10p' "$0"; exit 0 ;;
        --)           shift; CMD=("$@"); break ;;
        *)            CMD=("$@"); break ;;
    esac
    shift
done

# ------------------------------------------------------------ prerequisites
command -v docker >/dev/null || die "Docker is not installed."
docker info >/dev/null 2>&1 || die "Cannot talk to the Docker daemon. Is it running, and is $(id -un) in the 'docker' group? (sudo usermod -aG docker \$USER, then log out/in)"
if docker compose version >/dev/null 2>&1; then COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null; then COMPOSE=(docker-compose)
else die "Docker Compose is not installed (package docker-compose / docker-compose-plugin)."
fi
docker buildx version >/dev/null 2>&1 || export DOCKER_BUILDKIT=0  # classic builder works too

# ------------------------------------------------------------ host identity
HOST_UID="$(id -u)"; HOST_GID="$(id -g)"
if [[ "$HOST_UID" == 0 ]]; then
    HOST_UID="${SUDO_UID:-1000}"; HOST_GID="${SUDO_GID:-1000}"
fi
gid_of() { local g; for g in "$@"; do getent group "$g" | cut -d: -f3 && return; done; echo "${FALLBACK:-44}"; }
SERIAL_GID="$(FALLBACK=20 gid_of dialout uucp)"     # Debian/Ubuntu: dialout, Arch/Fedora-ish: uucp
VIDEO_GID="$(FALLBACK=44 gid_of video)"
RENDER_GID="$(FALLBACK="$VIDEO_GID" gid_of render)"
INPUT_GID="$(FALLBACK="$VIDEO_GID" gid_of input)"

# Host dirs must exist *before* docker sees them, otherwise Docker creates
# them as root and colcon cannot write into them.
mkdir -p ../.ros2_ws/{build,install,log,history}
touch ../.ros2_ws/history/bash_history
for d in ../.ros2_ws/{build,install,log,history}; do
    if [[ "$(stat -c %u "$d")" != "$HOST_UID" ]]; then
        info "Fixing ownership of root-owned $d (left by an older setup)"
        docker run --rm -v "$(readlink -f "$d"):/d" ubuntu:24.04 chown -R "$HOST_UID:$HOST_GID" /d \
            || echo "WARN: could not chown $d; the container entrypoint will retry" >&2
    fi
done

# ------------------------------------------------------------ display
DISPLAY="${DISPLAY:-}"; WAYLAND_DISPLAY_CONTAINER=""; WAYLAND_SOCKET_PATH=/dev/null
QT_QPA_PLATFORM=xcb; XAUTHORITY_PATH=/dev/null

if [[ -n "${WAYLAND_DISPLAY:-}" ]]; then
    if [[ "$WAYLAND_DISPLAY" == /* ]]; then sock="$WAYLAND_DISPLAY"
    else sock="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/$WAYLAND_DISPLAY"; fi
    if [[ -S "$sock" ]]; then WAYLAND_SOCKET_PATH="$sock"; WAYLAND_DISPLAY_CONTAINER=wayland-0; fi
fi
if [[ -n "$DISPLAY" ]]; then
    n="${DISPLAY##*:}"; n="${n%%.*}"
    if [[ "$DISPLAY" == :* && -S "/tmp/.X11-unix/X$n" ]] || [[ "$DISPLAY" != :* ]]; then
        command -v xhost >/dev/null && xhost "+SI:localuser:$(id -un)" >/dev/null 2>&1 || true
        # The container has its own hostname, so rewrite the X cookie as a
        # wildcard ("ffff") entry that matches any host (GNOME/KDE/XFCE/...).
        src_auth="${XAUTHORITY:-$HOME/.Xauthority}"
        XAUTH_FILE="$(readlink -f ../.ros2_ws)/docker.xauth"
        : > "$XAUTH_FILE"
        if command -v xauth >/dev/null && [[ -r "$src_auth" ]]; then
            xauth -f "$src_auth" nlist "$DISPLAY" 2>/dev/null | sed -e 's/^..../ffff/' \
                | xauth -f "$XAUTH_FILE" nmerge - 2>/dev/null || true
        fi
        [[ -s "$XAUTH_FILE" ]] || { [[ -r "$src_auth" ]] && cp "$src_auth" "$XAUTH_FILE"; } || true
        chmod 644 "$XAUTH_FILE"
        XAUTHORITY_PATH="$XAUTH_FILE"
    else
        echo "WARN: X socket for DISPLAY=$DISPLAY not found; using Wayland if possible." >&2
        DISPLAY=""
    fi
fi
if [[ -z "$DISPLAY" ]]; then
    if [[ "$WAYLAND_SOCKET_PATH" != /dev/null ]]; then QT_QPA_PLATFORM=wayland
    else echo "WARN: no X11/Wayland display found -- GUI apps (RViz, Gazebo GUI) will not open. Use headless:=true." >&2; fi
fi
LIBGL_ALWAYS_SOFTWARE="${LIBGL_ALWAYS_SOFTWARE:-$([[ -d /dev/dri ]] && echo 0 || echo 1)}"

# ------------------------------------------------------------ GPU
COMPOSE_FILE=docker-compose.yml
if [[ "$USE_GPU" == auto ]] && command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1 \
   && docker info --format '{{json .Runtimes}}' 2>/dev/null | grep -q '"nvidia"'; then
    COMPOSE_FILE+=:docker-compose.nvidia.yml
    info "NVIDIA GPU + container toolkit detected: GPU passthrough enabled"
elif command -v nvidia-smi >/dev/null && [[ "$USE_GPU" == auto ]]; then
    echo "WARN: NVIDIA GPU found but nvidia-container-toolkit is not configured for Docker; using Mesa/DRI." >&2
fi

# ------------------------------------------------------------ .env (lets plain `docker compose` work too)
cat > .env <<EOF
# Generated by run.sh for this host -- do not commit.
COMPOSE_FILE=$COMPOSE_FILE
CONTAINER_USER=omni_robot
HOST_UID=$HOST_UID
HOST_GID=$HOST_GID
SERIAL_GID=$SERIAL_GID
VIDEO_GID=$VIDEO_GID
RENDER_GID=$RENDER_GID
INPUT_GID=$INPUT_GID
DISPLAY=$DISPLAY
WAYLAND_DISPLAY_CONTAINER=$WAYLAND_DISPLAY_CONTAINER
WAYLAND_SOCKET_PATH=$WAYLAND_SOCKET_PATH
XAUTHORITY_PATH=$XAUTHORITY_PATH
QT_QPA_PLATFORM=$QT_QPA_PLATFORM
LIBGL_ALWAYS_SOFTWARE=$LIBGL_ALWAYS_SOFTWARE
ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-0}
ROS_NETWORK_INTERFACE=${ROS_NETWORK_INTERFACE:-}
EOF
export COMPOSE_FILE
DC=("${COMPOSE[@]}")

# ------------------------------------------------------------ build
IMAGE=ros2-jazzy-omni-slam:latest
img_ids="$(docker image inspect "$IMAGE" --format '{{index .Config.Labels "omni.uid"}}:{{index .Config.Labels "omni.gid"}}' 2>/dev/null || true)"
if (( FORCE_BUILD )) || [[ "$img_ids" != "$HOST_UID:$HOST_GID" ]]; then
    info "Building $IMAGE for UID:GID $HOST_UID:$HOST_GID (first build takes 10-20 min)..."
    "${DC[@]}" build
fi
(( BUILD_ONLY )) && { info "Image built."; exit 0; }

# ------------------------------------------------------------ start
# Remove a stale container of the same name left by another compose project.
if cid="$(docker ps -aq -f name='^ros2_jazzy_omni_slam$')" && [[ -n "$cid" ]]; then
    wd="$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project.working_dir" }}' "$cid" 2>/dev/null || true)"
    [[ "$wd" == "$PWD" ]] || { info "Removing old container from another setup"; docker rm -f "$cid" >/dev/null; }
fi
"${DC[@]}" up -d --remove-orphans ros2

if ((${#CMD[@]})); then
    if ((${#CMD[@]} == 1)); then cmdline="${CMD[0]}"; else cmdline="$(printf '%q ' "${CMD[@]}")"; fi
    tty_flag=(); [[ -t 0 && -t 1 ]] || tty_flag=(-T)
    exec "${DC[@]}" exec "${tty_flag[@]}" ros2 bash -ic "$cmdline"
fi
info "Inside the container: cd ~/ros2_ws && colcon build --symlink-install   (alias: cb)"
exec "${DC[@]}" exec ros2 bash
