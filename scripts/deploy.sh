#!/usr/bin/env bash
# Deploys the launcher UI, home-gesture watcher and systemd units to the Pi.
# Run from a Mac that already has an 'audi-mmi-pi' entry in ~/.ssh/config
# with working key-based auth (see docs/network-notes.md for finding the IP).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="audi-mmi-pi"

echo "==> Ordner auf dem Pi anlegen"
ssh "$HOST" "sudo mkdir -p /opt/audi-mmi/native-launcher/assets /opt/audi-mmi/bin /opt/audi-mmi/carplay"

echo "==> Launcher-Dateien kopieren"
scp -q "$REPO_DIR/native-launcher/launcher.py" "$HOST":/tmp/audi-mmi-launcher.py
scp -q "$REPO_DIR/native-launcher/assets/alps-background.png" "$HOST":/tmp/audi-mmi-alps-background.png
scp -q "$REPO_DIR/bin/kiosk-runner.sh" "$REPO_DIR/bin/touch-home-watcher.py" "$HOST":/tmp/

echo "==> systemd-Units und udev-Regel kopieren"
scp -q "$REPO_DIR"/systemd/*.service "$HOST":/tmp/
scp -q "$REPO_DIR"/carplay/99-carlinkit.rules "$HOST":/tmp/
ssh "$HOST" "sudo install -m 644 /tmp/audi-mmi-launcher.py /opt/audi-mmi/native-launcher/launcher.py && \
  sudo install -m 644 /tmp/audi-mmi-alps-background.png /opt/audi-mmi/native-launcher/assets/alps-background.png && \
  sudo install -m 755 /tmp/kiosk-runner.sh /tmp/touch-home-watcher.py /opt/audi-mmi/bin/ && \
  sudo mv /tmp/audi-mmi-kiosk.service /tmp/audi-mmi-home-watcher.service /tmp/audi-mmi-firstboot.service /etc/systemd/system/ && \
  sudo chown root:root /etc/systemd/system/audi-mmi-*.service && \
  sudo mv /tmp/99-carlinkit.rules /etc/udev/rules.d/ && \
  sudo udevadm control --reload-rules && \
  sudo systemctl daemon-reload && \
  sudo systemctl enable --now audi-mmi-kiosk.service && \
  sudo systemctl enable --now audi-mmi-home-watcher.service"

echo "==> Fertig. Status:"
ssh "$HOST" "systemctl is-active audi-mmi-kiosk.service audi-mmi-home-watcher.service"
