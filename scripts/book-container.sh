#!/usr/bin/env bash
set -euo pipefail

action="${1:?usage: book-container.sh setup|run IMAGE [COMMAND...]}"
image="${2:?image required}"
shift 2
project="$(pwd -P)"
[[ "$action" == run || -f "$project/Dockerfile" ]] || { echo "Run this task from its book folder." >&2; exit 2; }

docker_cmd=(docker)
if ! docker info >/dev/null 2>&1; then
  if [[ "${BOOK_DOCKER:-}" == pkexec ]]; then
    docker_cmd=(pkexec docker)
  else
    docker_cmd=(sudo docker)
  fi
fi

case "$action" in
  setup)
    "${docker_cmd[@]}" build --progress=plain -t "$image" "$@" "$project"
    ;;
  setup-editor)
    "${docker_cmd[@]}" build --progress=plain -t "$image" "$@" "$project/../scripts/editor"
    ;;
  run)
    "${docker_cmd[@]}" image inspect "$image" >/dev/null 2>&1 || {
      if [[ "$image" == *-editor ]]; then
        echo 'the editor image is missing. run: mise run editor:setup' >&2
      else
        echo 'the book image is missing. run: mise run setup' >&2
      fi
      exit 1
    }
    umask 077
    mkdir -p code exercises .state/home
    memory="${BOOK_MEMORY:-16g}"
    [[ "$memory" =~ ^[1-9][0-9]*[mg]$ ]] || { echo 'BOOK_MEMORY must be a positive size such as 16g.' >&2; exit 2; }
    args=(run --rm --init --read-only --cap-drop=ALL
      --security-opt=no-new-privileges --pids-limit=2048
      --memory="$memory" --memory-swap="$memory"
      --shm-size=2g
      --user "${BOOK_UID:-$(id -u)}:${BOOK_GID:-$(id -g)}"
      --tmpfs /tmp:rw,nosuid,nodev,size=2g
      --workdir /workspace
      --env HOME=/workspace/.state/home
      --env USER=learner
      --env LOGNAME=learner
      --env XDG_CACHE_HOME=/workspace/.state/cache
      --env TERM="${TERM:-xterm-256color}"
      --env COLORTERM="${COLORTERM:-truecolor}"
      --env PYTHONUNBUFFERED=1
      --mount "type=bind,src=$project/code,dst=/workspace/code"
      --mount "type=bind,src=$project/exercises,dst=/workspace/exercises"
      --mount "type=bind,src=$project/.state,dst=/workspace/.state")
    args+=(--mount "type=bind,src=$project/../scripts,dst=/opt/book-tools,readonly")
    [[ ! -f study.sh ]] || args+=(--mount "type=bind,src=$project/study.sh,dst=/opt/study.sh,readonly")
    if [[ -n "${BOOK_ENV_FILE:-}" ]]; then
      env_file="$(realpath -- "$BOOK_ENV_FILE")"
      [[ -f "$env_file" ]] || { echo 'BOOK_ENV_FILE must name an existing private environment file.' >&2; exit 2; }
      args+=(--env-file "$env_file")
    fi
    gpu="${BOOK_GPU:-auto}"
    case "$gpu" in auto|0|1) ;; *) echo 'BOOK_GPU must be auto, 0, or 1.' >&2; exit 2 ;; esac
    if [[ "${BOOK_KVM:-0}" == 1 ]]; then
      [[ -e /dev/kvm ]] || { echo "/dev/kvm is unavailable." >&2; exit 1; }
      args+=(--device /dev/kvm --group-add "$(stat -c %g /dev/kvm)")
    fi
    if [[ -n "${BOOK_PORT:-}" ]]; then
      [[ "$BOOK_PORT" =~ ^[0-9]+$ ]] && ((BOOK_PORT > 1023 && BOOK_PORT < 65536)) || {
        echo "BOOK_PORT must be a port from 1024 to 65535." >&2; exit 2;
      }
    fi
    if [[ -n "${BOOK_NETWORK:-}" ]]; then
      [[ "$BOOK_NETWORK" =~ ^[a-zA-Z0-9_.-]+$ && "$BOOK_NETWORK" != host ]] || {
        echo 'BOOK_NETWORK must be a named Docker network, bridge, or none.' >&2; exit 2;
      }
      args+=(--network "$BOOK_NETWORK")
    fi
    if [[ "$gpu" != 0 ]]; then
      gpu_args=(--gpus all)
      # Use the live device nodes even when the system CDI file has older numbers.
      for device in /dev/nvidia-uvm /dev/nvidia-uvm-tools; do
        if [[ -c "$device" ]]; then
          gpu_args+=(--device "$device" --mount "type=bind,src=$device,dst=$device")
        fi
      done
      if "${docker_cmd[@]}" "${args[@]}" "${gpu_args[@]}" "$image" python -c \
          'import signal; signal.alarm(30)
import ctypes as c
cuda = c.CDLL("libcuda.so.1")
context, memory = c.c_void_p(), c.c_uint64()
def check(result):
    assert result == 0, f"CUDA error {result}"
check(cuda.cuInit(0))
check(cuda.cuDevicePrimaryCtxRetain(c.byref(context), 0))
check(cuda.cuCtxSetCurrent(context))
check(cuda.cuMemAlloc_v2(c.byref(memory), c.c_size_t(16)))
check(cuda.cuMemsetD32_v2(memory, c.c_uint(7), c.c_size_t(4)))
result = (c.c_uint * 4)()
check(cuda.cuMemcpyDtoH_v2(result, memory, c.c_size_t(16)))
assert list(result) == [7] * 4
check(cuda.cuMemFree_v2(memory))
check(cuda.cuDevicePrimaryCtxRelease(0))' \
          >.state/gpu.log 2>&1; then
        args+=("${gpu_args[@]}")
        gpu=1
        echo 'using nvidia gpu' >&2
      elif [[ "$gpu" == 1 ]]; then
        echo 'gpu unavailable. see .state/gpu.log; use BOOK_GPU=0 for cpu.' >&2
        exit 1
      else
        gpu=0
        echo 'using cpu; gpu unavailable. details in .state/gpu.log' >&2
      fi
    fi
    args+=(--env "BOOK_GPU=$gpu")
    [[ "$gpu" != 0 ]] || args+=(--env CUDA_VISIBLE_DEVICES=-1 --env NVIDIA_VISIBLE_DEVICES=void --env JAX_PLATFORMS=cpu)
    [[ -z "${BOOK_PORT:-}" ]] || args+=(-p "127.0.0.1:$BOOK_PORT:$BOOK_PORT")
    [[ ! -t 0 || ! -t 1 ]] || args+=(-t)
    "${docker_cmd[@]}" "${args[@]}" -i "$image" "${@:-bash}"
    ;;
  *)
    echo "usage: book-container.sh setup|run IMAGE [COMMAND...]" >&2
    exit 2
    ;;
esac
