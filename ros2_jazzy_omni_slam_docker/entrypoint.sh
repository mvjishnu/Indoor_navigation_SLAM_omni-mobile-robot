#!/usr/bin/env bash
# Container entrypoint: makes the bind-mounted workspace usable and writes a
# CycloneDDS config for whatever network this host is on, then runs CMD.
set -eo pipefail

# 1. Bind-mounted dirs that Docker auto-created are owned by root -> fix them.
for d in "$HOME/ros2_ws/build" "$HOME/ros2_ws/install" "$HOME/ros2_ws/log" "$HOME/.history"; do
    mkdir -p "$d" 2>/dev/null || sudo mkdir -p "$d"
    if [ "$(stat -c %u "$d")" != "$(id -u)" ]; then
        sudo chown -R "$(id -u):$(id -g)" "$d" || echo "WARN: cannot chown $d" >&2
    fi
done

# Give host-only supplementary GIDs (render, uucp, input, ...) a name so
# `groups`/`id` don't complain, and silence Ubuntu's sudo hint.
for g in $(id -G); do
    getent group "$g" >/dev/null || sudo groupadd -g "$g" "host_$g" 2>/dev/null || true
done
touch "$HOME/.sudo_as_admin_successful" 2>/dev/null || true

# 2. CycloneDDS: bind to the default-route interface (host networking), plus
#    loopback. With no network at all, fall back to localhost-only discovery.
CYCLONE_XML=/tmp/cyclonedds.xml
if [ -n "${CYCLONEDDS_URI:-}" ] && [ "${CYCLONEDDS_URI}" != "file://${CYCLONE_XML}" ]; then
    : # user supplied their own config; leave it alone
else
    IFACE="${ROS_NETWORK_INTERFACE:-$(awk '$2 == "00000000" && $1 != "Iface" {print $1; exit}' /proc/net/route 2>/dev/null)}"
    if [ -n "$IFACE" ] && [ -e "/sys/class/net/$IFACE" ]; then
        cat > "$CYCLONE_XML" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config"><Domain Id="any"><General><Interfaces><NetworkInterface name="lo" priority="10" multicast="true"/><NetworkInterface name="$IFACE" priority="0" multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>
EOF
    else
        cat > "$CYCLONE_XML" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS xmlns="https://cdds.io/config"><Domain Id="any"><General><Interfaces><NetworkInterface name="lo"/></Interfaces><AllowMulticast>false</AllowMulticast></General><Discovery><ParticipantIndex>auto</ParticipantIndex><MaxAutoParticipantIndex>120</MaxAutoParticipantIndex><Peers><Peer address="localhost"/></Peers></Discovery></Domain></CycloneDDS>
EOF
    fi
    export CYCLONEDDS_URI="file://${CYCLONE_XML}"
fi

# 3. Qt needs XDG_RUNTIME_DIR to exist with 0700.
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ ! -d "$XDG_RUNTIME_DIR" ]; then
    sudo mkdir -p "$XDG_RUNTIME_DIR" && sudo chown "$(id -u):$(id -g)" "$XDG_RUNTIME_DIR" && chmod 0700 "$XDG_RUNTIME_DIR"
fi

source /opt/ros/jazzy/setup.bash
[ -f "$HOME/ros2_ws/install/setup.bash" ] && source "$HOME/ros2_ws/install/setup.bash"

exec "$@"
