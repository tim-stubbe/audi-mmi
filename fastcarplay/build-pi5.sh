#!/usr/bin/env bash
set -euo pipefail
COMMIT=f483456318344710d2890fc7ee0d67608892dea2
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${1:-/tmp/FastCarPlay-audi-mmi}"
git clone https://github.com/niellun/FastCarPlay.git "$WORK"
git -C "$WORK" checkout "$COMMIT"
git -C "$WORK" apply "$HERE/patches/audi-mmi.patch"
cp "$HERE/background.bmp" "$WORK/src/resource/background.bmp"
make -C "$WORK" clean release
strip --strip-unneeded "$WORK/out/app"
cp "$WORK/out/app" "$HERE/fastcarplay"
