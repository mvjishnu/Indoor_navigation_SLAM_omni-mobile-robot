#!/usr/bin/env bash
# Build (or rebuild) the image for this host. Same as ./run.sh --build-only
exec "$(dirname "$(readlink -f "$0")")/run.sh" --build-only "$@"
