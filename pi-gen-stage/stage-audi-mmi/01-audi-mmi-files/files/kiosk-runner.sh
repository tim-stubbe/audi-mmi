#!/bin/bash
# Owns the single 'cage' Wayland kiosk session: runs the native GTK launcher,
# and on request hands the screen over to the react-carplay AppImage by
# exiting cage and starting a fresh cage instance for it. cage only ever
# hosts one client for its lifetime, so app-switching means restarting it,
# not hiding a window - the handoff takes under a second in practice.
set -u

MARKER="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/audi-mmi/next-app"
CARPLAY_APPIMAGE=/opt/audi-mmi/carplay/react-carplay-4.0.5-arm64.AppImage
KIES_DRIVE_EXECUTABLE=/opt/audi-mmi/kies-drive/kies-drive

mkdir -p "$(dirname "$MARKER")"

while true; do
  rm -f "$MARKER"
  cage -- /usr/bin/python3 /opt/audi-mmi/native-launcher/launcher.py

  if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "carplay" ] && [ -x "$CARPLAY_APPIMAGE" ]; then
    rm -f "$MARKER"
    cage -- "$CARPLAY_APPIMAGE" --no-sandbox
  elif [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "kies-drive" ] && [ -x "$KIES_DRIVE_EXECUTABLE" ]; then
    rm -f "$MARKER"
    cage -- "$KIES_DRIVE_EXECUTABLE"
  fi
done
