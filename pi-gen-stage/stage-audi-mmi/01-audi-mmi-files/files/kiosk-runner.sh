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
CARPLAY_STATE_DIR="${HOME:-/tmp}/.local/state/audi-mmi"
CARPLAY_LOG="$CARPLAY_STATE_DIR/carplay.log"
COMPAT_LIB_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/audi-mmi/lib"

mkdir -p "$(dirname "$MARKER")" "$CARPLAY_STATE_DIR" "$COMPAT_LIB_DIR"

# react-carplay 4.0.5 ships with an AppImage runtime linked against the
# unversioned libz.so name. Debian provides the ABI-compatible library as
# libz.so.1, so expose that name in a private runtime directory. This avoids
# installing development packages just to obtain the linker symlink.
if [ -e /lib/aarch64-linux-gnu/libz.so.1 ]; then
  ln -sfn /lib/aarch64-linux-gnu/libz.so.1 "$COMPAT_LIB_DIR/libz.so"
elif [ -e /usr/lib/aarch64-linux-gnu/libz.so.1 ]; then
  ln -sfn /usr/lib/aarch64-linux-gnu/libz.so.1 "$COMPAT_LIB_DIR/libz.so"
fi

while true; do
  rm -f "$MARKER"
  cage -- /usr/bin/python3 /opt/audi-mmi/native-launcher/launcher.py

  if [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "carplay" ] && [ -x "$CARPLAY_APPIMAGE" ]; then
    rm -f "$MARKER"
    {
      printf '\n=== react-carplay start %s ===\n' "$(date --iso-8601=seconds)"
      LD_LIBRARY_PATH="$COMPAT_LIB_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
        ELECTRON_OZONE_PLATFORM_HINT=wayland \
        cage -- "$CARPLAY_APPIMAGE" \
          --no-sandbox \
          --ozone-platform=wayland \
          --enable-features=UseOzonePlatform \
          --disable-gpu-sandbox \
          --disable-dev-shm-usage
      printf 'react-carplay exit status: %s\n' "$?"
    } >>"$CARPLAY_LOG" 2>&1
  elif [ -f "$MARKER" ] && [ "$(cat "$MARKER")" = "kies-drive" ] && [ -x "$KIES_DRIVE_EXECUTABLE" ]; then
    rm -f "$MARKER"
    cage -- "$KIES_DRIVE_EXECUTABLE"
  fi
done
