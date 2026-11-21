#!/usr/bin/env bash
# Standalone Raspberry Pi/Linux RPLIDAR C1 bring-up using SLAMTEC's SDK.
set -euo pipefail

testing_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sdk_dir="$testing_dir/.rplidar_sdk"
scanner="$sdk_dir/output/Linux/Release/ultra_simple"

usage() {
    cat <<'EOF'
Usage: ./lidar_c1.sh [PORT [BAUD]]
       ./lidar_c1.sh --setup
       ./lidar_c1.sh --list

Defaults: /dev/ttyUSB0, 460800 baud (RPLIDAR C1).
The SDK is downloaded and built on first use. No ROS installation is needed.
--setup  Download/build only, without opening the LiDAR.
--list   List USB/UART ports; prefer /dev/serial/by-id/... for a stable name.
Press Ctrl+C to stop scanning and stop the motor.
EOF
}

list_ports() {
    local ports=()
    shopt -s nullglob
    ports=(/dev/serial/by-id/* /dev/ttyUSB* /dev/ttyACM* /dev/ttyAMA*)
    if ((${#ports[@]})); then
        printf '%s\n' "${ports[@]}"
    else
        printf 'No serial ports found. Check the USB cable and LiDAR power.\n'
    fi
}

setup_sdk() {
    local command
    for command in git make g++; do
        if ! command -v "$command" >/dev/null 2>&1; then
            printf 'Missing %s. On Raspberry Pi OS/Ubuntu, run:\n' "$command" >&2
            printf '  sudo apt update && sudo apt install -y git build-essential\n' >&2
            exit 1
        fi
    done
    if [[ ! -d "$sdk_dir" ]]; then
        git clone --depth 1 https://github.com/Slamtec/rplidar_sdk.git "$sdk_dir"
    fi
    if [[ ! -f "$sdk_dir/Makefile" ]]; then
        printf 'Incomplete SDK at %s; move it aside and run --setup again.\n' "$sdk_dir" >&2
        exit 1
    fi
    # Limit build parallelism to keep memory use modest on the Pi 4.
    make -C "$sdk_dir" -j2
    if [[ ! -x "$scanner" ]]; then
        printf 'Build did not produce %s\n' "$scanner" >&2
        exit 1
    fi
}

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
    --list) list_ports; exit 0 ;;
    --setup) setup_sdk; exit 0 ;;
    -*) usage >&2; exit 2 ;;
esac
if (($# > 2)); then
    usage >&2
    exit 2
fi
if [[ "$(uname -s)" != Linux ]]; then
    printf 'Run this test on the Raspberry Pi (Linux).\n' >&2
    exit 1
fi

port="${1:-/dev/ttyUSB0}"
baud="${2:-460800}"
if [[ ! "$baud" =~ ^[1-9][0-9]*$ ]]; then
    printf 'Baud rate must be a positive integer.\n' >&2
    exit 2
fi
if [[ ! -c "$port" ]]; then
    printf 'Serial device not found: %s\nAvailable ports:\n' "$port" >&2
    list_ports >&2
    exit 1
fi
if [[ ! -r "$port" || ! -w "$port" ]]; then
    printf 'No read/write access to %s. Run:\n' "$port" >&2
    printf '  sudo usermod -aG dialout "%s"\n' "$(id -un)" >&2
    printf 'Then log out and back in, and retry.\n' >&2
    exit 1
fi
if [[ ! -x "$scanner" ]]; then
    setup_sdk
fi
printf 'RPLIDAR C1: %s @ %s baud. Ctrl+C stops the motor.\n' "$port" "$baud"
exec "$scanner" --channel --serial "$port" "$baud"
