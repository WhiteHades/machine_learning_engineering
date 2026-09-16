#!/usr/bin/env bash
set -euo pipefail

root="${MISE_CONFIG_ROOT:-$PWD}"
root="$(cd -- "$root" && pwd -P)"
[[ -f "$root/book.env" ]] || { echo 'Run this command from a book folder.' >&2; exit 2; }
# This file is tracked setup configuration, not a credentials file.
source "$root/book.env"
BOOK_IMAGE="${BOOK_IMAGE_OVERRIDE:-$BOOK_IMAGE}"
runner="$root/../scripts/book-container.sh"
cd "$root"

prepare_dirs() {
    mkdir -p code exercises .state/home .state/cache .state/notebooks
}

fetch_reference() {
    prepare_dirs
    if [[ ! -d code/.git ]]; then
        [[ -z "$(ls -A code)" ]] || { echo 'code/ is not empty. Preserve its contents before fetching.' >&2; exit 1; }
        git -C code init -q
        git -C code remote add origin "$AUTHOR_URL"
    fi
    if ! git -C code rev-parse --verify HEAD >/dev/null 2>&1; then
        git -C code fetch --depth 1 origin "$AUTHOR_REVISION"
        git -C code checkout --detach FETCH_HEAD
    fi
    actual="$(git -C code rev-parse HEAD)"
    [[ "$actual" == "$AUTHOR_REVISION" ]] || {
        echo "Reference revision differs: $actual. Setup will not overwrite it." >&2
        exit 1
    }
}

run_container() {
    mkdir -p .state/ultralytics
    bash "$runner" run "$BOOK_IMAGE" env \
        BOOK_KIND="$BOOK_KIND" \
        PYTHONPATH=/workspace/exercises:/workspace/code:/workspace/code/pkg \
        HF_HOME=/workspace/.state/huggingface \
        TORCH_HOME=/workspace/.state/torch \
        TORCHINDUCTOR_CACHE_DIR=/workspace/.state/torchinductor \
        TRITON_CACHE_DIR=/workspace/.state/triton \
        TIKTOKEN_CACHE_DIR=/workspace/.state/tiktoken \
        MPLCONFIGDIR=/workspace/.state/matplotlib \
        YOLO_CONFIG_DIR=/workspace/.state/ultralytics \
        JUPYTER_CONFIG_DIR=/workspace/.state/jupyter \
        JUPYTER_DATA_DIR=/workspace/.state/jupyter-data \
        JUPYTER_RUNTIME_DIR=/workspace/.state/jupyter-runtime \
        CHAINLIT_APP_ROOT=/workspace/.state \
        "$@"
}

validate_path() {
    local target="${1:-}" resolved
    case "$target" in code|code/*|exercises|exercises/*) ;; *) echo 'Use a path under code/ or exercises/.' >&2; exit 2 ;; esac
    resolved="$(realpath -m -- "$root/$target")"
    case "$resolved" in "$root/code"|"$root/code/"*|"$root/exercises"|"$root/exercises/"*) ;; *) echo 'Path leaves the study directories.' >&2; exit 2 ;; esac
}

action="${1:-help}"
shift || true
case "$action" in
    fetch) fetch_reference ;;
    setup)
        [[ -z "${BOOK_IMAGE_OVERRIDE:-}" ]] || { echo 'Build the base image without BOOK_IMAGE_OVERRIDE.' >&2; exit 2; }
        fetch_reference
        bash "$runner" setup "$BOOK_IMAGE"
        BOOK_GPU=0 run_container python /opt/book-tools/verify-python.py
        ;;
    doctor)
        for tool in git docker mise; do command -v "$tool" || exit 1; done
        printf 'Image: %s\nExpected author revision: %s\n' "$BOOK_IMAGE" "$AUTHOR_REVISION"
        if [[ -d code/.git ]]; then
            current_revision="$(git -C code rev-parse HEAD)"
            printf 'Current author revision: %s\n' "$current_revision"
            [[ "$current_revision" == "$AUTHOR_REVISION" ]] || { echo 'Author revision differs from book.env.' >&2; exit 1; }
            git -C code status --short
        else
            echo 'Reference not downloaded. Run mise run setup.'
            exit 1
        fi
        docker_cmd=(docker)
        if ! docker info >/dev/null 2>&1; then
            if [[ "${BOOK_DOCKER:-}" == pkexec ]]; then docker_cmd=(pkexec docker); else docker_cmd=(sudo docker); fi
        fi
        "${docker_cmd[@]}" info --format '{{.ServerVersion}}'
        "${docker_cmd[@]}" image inspect "$BOOK_IMAGE" --format '{{.Id}}'
        ;;
    run)
        target="${1:-}"; shift || true
        validate_path "$target"
        [[ -f "$target" && "$target" == *.py ]] || { echo 'Supply an existing Python file.' >&2; exit 2; }
        run_container bash -c 'cd -- "$1"; shift; exec python "$@"' \
            _ "/workspace/${target%/*}" "${target##*/}" "$@"
        ;;
    lab)
        target="${1:-exercises}"
        if [[ "$BOOK_KIND" == keras && "$target" =~ ^[0-9]{1,2}$ ]]; then
            chapter="$(printf '%02d' "$((10#$target))")"
            matches=(code/chapter"$chapter"_*.ipynb)
            target="${matches[0]}"
        fi
        validate_path "$target"
        [[ -e "$target" ]] || { echo "Missing path: $target" >&2; exit 2; }
        port="${BOOK_PORT:-8888}"
        BOOK_PORT="$port" run_container jupyter lab --ip=0.0.0.0 --port="$port" \
            --no-browser --ServerApp.root_dir=/workspace "/workspace/$target"
        ;;
    notebook)
        target="${1:-}"
        validate_path "$target"
        [[ -f "$target" && "$target" == *.ipynb ]] || { echo 'Supply an existing notebook.' >&2; exit 2; }
        run_container jupyter nbconvert --to notebook --execute \
            --ExecutePreprocessor.timeout="${BOOK_CELL_TIMEOUT:-600}" \
            --output-dir=/workspace/.state/notebooks "/workspace/$target"
        ;;
    test)
        target="${1:-exercises}"
        validate_path "$target"
        [[ "$target" == exercises || "$target" == exercises/* ]] || { echo 'test checks your work under exercises/.' >&2; exit 2; }
        shift || true
        run_container python -m pytest -o cache_dir=/workspace/.state/pytest "$target" "$@"
        ;;
    shell) run_container bash "$@" ;;
    verify) run_container python /opt/book-tools/verify-python.py ;;
    gpu-verify) BOOK_GPU=1 run_container python /opt/book-tools/verify-python.py ;;
    editor-setup)
        [[ -z "${BOOK_IMAGE_OVERRIDE:-}" ]] || { echo 'Build the editor without BOOK_IMAGE_OVERRIDE.' >&2; exit 2; }
        prepare_dirs
        python "$root/../scripts/editor/snapshot.py" "$root/.state/editor"
        bash "$runner" setup-editor "${BOOK_IMAGE}-editor" --build-arg "BOOK_BASE_IMAGE=$BOOK_IMAGE"
        BOOK_IMAGE="${BOOK_IMAGE}-editor"
        BOOK_GPU=0 run_container bash /opt/book-tools/editor/start.sh --setup
        ;;
    edit)
        target="${1:-exercises}"
        [[ $# -le 1 ]] || { echo 'Supply one exercise path.' >&2; exit 2; }
        validate_path "$target"
        [[ "$target" == exercises || "$target" == exercises/* ]] || { echo 'Edit your work under exercises/; keep code/ as reference.' >&2; exit 2; }
        [[ -d "$target" || "$target" == *.py || "$target" == *.ipynb ]] || { echo 'Supply a directory, .py file, or .ipynb file.' >&2; exit 2; }
        [[ -d "$target" || -d "$(dirname -- "$target")" ]] || { echo 'Create the parent exercise directory first.' >&2; exit 2; }
        BOOK_IMAGE="${BOOK_IMAGE}-editor"
        run_container bash /opt/book-tools/editor/start.sh "/workspace/$target"
        ;;
    editor-verify)
        BOOK_IMAGE="${BOOK_IMAGE}-editor"
        run_container bash /opt/book-tools/editor/start.sh --verify
        ;;
    *)
        echo 'Commands: setup, fetch, doctor, run FILE.py, lab [PATH], notebook FILE.ipynb, test [PATH], shell, verify, gpu-verify, editor-setup, edit [PATH], editor-verify'
        [[ "$action" == help ]]
        ;;
esac
