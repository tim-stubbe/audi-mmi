#!/usr/bin/env bash
# Deploys the launcher UI, home-gesture watcher and systemd units to the Pi.
# Run from a Mac that already has an 'audi-mmi-pi' entry in ~/.ssh/config
# with working key-based auth (see docs/network-notes.md for finding the IP).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="audi-mmi-pi"

echo "==> Ordner auf dem Pi anlegen"
ssh "$HOST" "sudo mkdir -p /opt/audi-mmi/launcher /opt/audi-mmi/bin /opt/audi-mmi/carplay && sudo chown -R tim:tim /opt/audi-mmi"

echo "==> Launcher-Dateien kopieren"
scp -q -r "$REPO_DIR"/launcher/* "$HOST":/opt/audi-mmi/launcher/
scp -q "$REPO_DIR"/bin/touch-home-watcher.py "$HOST":/opt/audi-mmi/bin/

echo "==> systemd-Units und udev-Regel kopieren"
scp -q "$REPO_DIR"/systemd/*.service "$HOST":/tmp/
scp -q "$REPO_DIR"/carplay/99-carlinkit.rules "$HOST":/tmp/
ssh "$HOST" "sudo mv /tmp/audi-mmi-ui.service /tmp/audi-mmi-home-watcher.service /etc/systemd/system/ && \
  sudo chown root:root /etc/systemd/system/audi-mmi-ui.service /etc/systemd/system/audi-mmi-home-watcher.service && \
  sudo mv /tmp/99-carlinkit.rules /etc/udev/rules.d/ && \
  sudo udevadm control --reload-rules && \
  sudo usermod -aG plugdev,input tim && \
  sudo systemctl daemon-reload && \
  sudo systemctl enable --now audi-mmi-ui.service && \
  sudo systemctl enable --now audi-mmi-home-watcher.service"

echo "==> Fertig. Status:"
ssh "$HOST" "systemctl is-active audi-mmi-ui.service audi-mmi-home-watcher.service"
