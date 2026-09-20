#!/usr/bin/env bash
# Installs an MMI application update over SSH. The target can be a local
# hostname or the Pi's stable Tailscale/MagicDNS name.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${MMI_PI_HOST:-audi-mmi-pi}"
VERSION="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)"
REMOTE_STAGE="/tmp/audi-mmi-update-${VERSION}"

echo "==> Update ${VERSION} für ${HOST} vorbereiten"
ssh "$HOST" "rm -rf '$REMOTE_STAGE' && mkdir -p '$REMOTE_STAGE/native-launcher/assets' '$REMOTE_STAGE/bin' '$REMOTE_STAGE/systemd' '$REMOTE_STAGE/carplay'"

scp -q "$REPO_DIR/native-launcher/launcher.py" "$HOST:$REMOTE_STAGE/native-launcher/launcher.py"
scp -q "$REPO_DIR/native-launcher/assets/alps-background.png" "$HOST:$REMOTE_STAGE/native-launcher/assets/alps-background.png"
scp -q "$REPO_DIR/bin/kiosk-runner.sh" "$REPO_DIR/bin/touch-home-watcher.py" "$HOST:$REMOTE_STAGE/bin/"
scp -q "$REPO_DIR"/systemd/*.service "$HOST:$REMOTE_STAGE/systemd/"
scp -q "$REPO_DIR/carplay/99-carlinkit.rules" "$HOST:$REMOTE_STAGE/carplay/"

echo "==> Dateien prüfen, sichern und atomar installieren"
ssh "$HOST" "sudo /bin/bash -s -- '$REMOTE_STAGE' '$VERSION'" <<'REMOTE_SCRIPT'
set -euo pipefail
STAGE="$1"
VERSION="$2"
BACKUP="/opt/audi-mmi/backups/$VERSION"

python3 -m py_compile "$STAGE/native-launcher/launcher.py" "$STAGE/bin/touch-home-watcher.py"
bash -n "$STAGE/bin/kiosk-runner.sh"

mkdir -p "$BACKUP/native-launcher/assets" "$BACKUP/bin" "$BACKUP/systemd" "$BACKUP/carplay"
cp -a /opt/audi-mmi/native-launcher/launcher.py "$BACKUP/native-launcher/" 2>/dev/null || true
cp -a /opt/audi-mmi/native-launcher/assets/alps-background.png "$BACKUP/native-launcher/assets/" 2>/dev/null || true
cp -a /opt/audi-mmi/bin/kiosk-runner.sh /opt/audi-mmi/bin/touch-home-watcher.py "$BACKUP/bin/" 2>/dev/null || true
cp -a /etc/systemd/system/audi-mmi-*.service "$BACKUP/systemd/" 2>/dev/null || true
cp -a /etc/udev/rules.d/99-carlinkit.rules "$BACKUP/carplay/" 2>/dev/null || true

rollback() {
  echo "Update fehlgeschlagen – vorherige Version wird wiederhergestellt." >&2
  cp -a "$BACKUP/native-launcher/launcher.py" /opt/audi-mmi/native-launcher/ 2>/dev/null || true
  cp -a "$BACKUP/native-launcher/assets/alps-background.png" /opt/audi-mmi/native-launcher/assets/ 2>/dev/null || true
  cp -a "$BACKUP/bin/"* /opt/audi-mmi/bin/ 2>/dev/null || true
  cp -a "$BACKUP/systemd/"* /etc/systemd/system/ 2>/dev/null || true
  cp -a "$BACKUP/carplay/99-carlinkit.rules" /etc/udev/rules.d/ 2>/dev/null || true
  systemctl daemon-reload
  systemctl restart audi-mmi-kiosk.service audi-mmi-home-watcher.service || true
}
trap rollback ERR

install -d /opt/audi-mmi/native-launcher/assets /opt/audi-mmi/bin /opt/audi-mmi/carplay
install -m 644 "$STAGE/native-launcher/launcher.py" /opt/audi-mmi/native-launcher/launcher.py
install -m 644 "$STAGE/native-launcher/assets/alps-background.png" /opt/audi-mmi/native-launcher/assets/alps-background.png
install -m 755 "$STAGE/bin/kiosk-runner.sh" "$STAGE/bin/touch-home-watcher.py" /opt/audi-mmi/bin/
install -m 644 "$STAGE/systemd/"*.service /etc/systemd/system/
install -m 644 "$STAGE/carplay/99-carlinkit.rules" /etc/udev/rules.d/99-carlinkit.rules
printf '%s\n' "$VERSION" > /opt/audi-mmi/VERSION

udevadm control --reload-rules
systemctl daemon-reload
systemctl enable audi-mmi-kiosk.service audi-mmi-home-watcher.service >/dev/null
systemctl restart audi-mmi-kiosk.service audi-mmi-home-watcher.service
sleep 2
systemctl is-active --quiet audi-mmi-kiosk.service
systemctl is-active --quiet audi-mmi-home-watcher.service

trap - ERR
rm -rf "$STAGE"
# Keep the three most recent rollback copies so the SD card does not fill up.
find /opt/audi-mmi/backups -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' \
  | sort -nr | tail -n +4 | cut -d' ' -f2- | xargs -r rm -rf
REMOTE_SCRIPT

echo "==> Update ${VERSION} läuft; beide MMI-Dienste sind aktiv."
