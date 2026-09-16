#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
export MISE_CONFIG_ROOT="$root"
exec bash "$root/../scripts/python-book.sh" "$@"
