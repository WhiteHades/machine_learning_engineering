#!/usr/bin/env bash
set -euo pipefail
root="${MISE_CONFIG_ROOT:-$PWD}"
cd -- "$root"
source book.env
[[ "$BOOK_KIND" == foundation ]] || { echo 'This task belongs to the Geron book.' >&2; exit 2; }
bash ../scripts/python-book.sh gpu-verify
bash ../scripts/book-container.sh setup "${BOOK_IMAGE}-appendix-e" --file "$PWD/Dockerfile.appendix-e"
BOOK_IMAGE_OVERRIDE="${BOOK_IMAGE}-appendix-e" BOOK_GPU=1 \
    bash ../scripts/python-book.sh shell -c 'python /opt/book-tools/verify-appendix-e.py'
