#!/usr/bin/env bash
set -euo pipefail
export HOME=/workspace/.state/editor/home
export XDG_CONFIG_HOME=/workspace/.state/editor/config
export XDG_DATA_HOME=/workspace/.state/editor/data
export XDG_STATE_HOME=/workspace/.state/editor/state
export XDG_CACHE_HOME=/workspace/.state/editor/cache
export XDG_RUNTIME_DIR=/tmp/book-editor-runtime
mkdir -p "$HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME/nvim" "$XDG_CACHE_HOME" "$XDG_RUNTIME_DIR"
mkdir -p "$JUPYTER_DATA_DIR/runtime"
chmod 700 "$XDG_RUNTIME_DIR"
[[ -f "$XDG_CONFIG_HOME/nvim/init.lua" ]] || { echo 'Run mise run editor:setup first.' >&2; exit 1; }
# Existing notebook configuration expects its tools below config/.venv.
runtime="$XDG_CONFIG_HOME/nvim/.venv"
mkdir -p "$runtime/bin" "$runtime/lib"
for tool in python python3 jupytext; do ln -sfn "/usr/local/bin/$tool" "$runtime/bin/$tool"; done
version="$(python -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}")')"
ln -sfn "/usr/local/lib/$version" "$runtime/lib/$version"
editor=(nvim -u /opt/book-tools/editor/bootstrap.lua)
if [[ "${1:-}" != --setup && ! -f "$XDG_DATA_HOME/nvim/rplugin.vim" ]]; then
    echo 'editor setup is incomplete. run: mise run editor:setup' >&2
    exit 1
fi
case "${1:-}" in
    --setup) "${editor[@]}" --headless '+luafile /opt/book-tools/editor/install.lua' ;;
    --verify) exec python /opt/book-tools/editor/verify.py ;;
    *)
        target="${1:-/workspace/exercises}"
        if [[ -d "$target" ]]; then cd -- "$target"; else cd -- "$(dirname -- "$target")"; fi
        exec "${editor[@]}" "$target"
        ;;
esac
