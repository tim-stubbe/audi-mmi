#!/usr/bin/env bash
# Creates the small application bundle attached to a tested GitHub release.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="${1:-$ROOT/dist/audi-mmi-update.tar.gz}"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/native-launcher/assets" "$STAGE/bin" "$STAGE/systemd" "$STAGE/carplay" "$STAGE/fastcarplay" "$(dirname "$OUTPUT")"
cp "$ROOT/native-launcher/launcher.py" "$STAGE/native-launcher/"
cp "$ROOT/native-launcher/assets/alps-background.png" "$STAGE/native-launcher/assets/"
cp "$ROOT/bin/kiosk-runner.sh" "$ROOT/bin/touch-home-watcher.py" "$ROOT/bin/audi-mmi-updater.py" "$STAGE/bin/"
cp "$ROOT/systemd/audi-mmi-kiosk.service" "$ROOT/systemd/audi-mmi-home-watcher.service" \
   "$ROOT/systemd/audi-mmi-update.service" "$ROOT/systemd/audi-mmi-update.timer" "$STAGE/systemd/"
cp "$ROOT/carplay/99-carlinkit.rules" "$STAGE/carplay/"
cp "$ROOT/fastcarplay/fastcarplay" "$ROOT/fastcarplay/settings.txt" \
   "$ROOT/fastcarplay/LICENSE" "$ROOT/fastcarplay/SOURCE.md" "$STAGE/fastcarplay/"

tar -C "$STAGE" -czf "$OUTPUT" .
echo "$OUTPUT"
