#!/bin/bash -e

install -d "${ROOTFS_DIR}/opt/audi-mmi/native-launcher"
install -d "${ROOTFS_DIR}/opt/audi-mmi/native-launcher/assets"
install -d "${ROOTFS_DIR}/opt/audi-mmi/bin"
install -d "${ROOTFS_DIR}/opt/audi-mmi/carplay"
install -d "${ROOTFS_DIR}/etc/systemd/system"
install -d "${ROOTFS_DIR}/etc/udev/rules.d"

install -m 644 files/launcher.py "${ROOTFS_DIR}/opt/audi-mmi/native-launcher/launcher.py"
install -m 644 files/assets/alps-background.png "${ROOTFS_DIR}/opt/audi-mmi/native-launcher/assets/alps-background.png"
install -m 755 files/kiosk-runner.sh "${ROOTFS_DIR}/opt/audi-mmi/bin/kiosk-runner.sh"
install -m 755 files/touch-home-watcher.py "${ROOTFS_DIR}/opt/audi-mmi/bin/touch-home-watcher.py"
install -m 755 files/audi-mmi-firstboot.sh "${ROOTFS_DIR}/opt/audi-mmi/bin/audi-mmi-firstboot.sh"
install -m 755 files/audi-mmi-updater.py "${ROOTFS_DIR}/opt/audi-mmi/bin/audi-mmi-updater.py"

install -m 644 files/audi-mmi-kiosk.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-kiosk.service"
install -m 644 files/audi-mmi-home-watcher.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-home-watcher.service"
install -m 644 files/audi-mmi-firstboot.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-firstboot.service"
install -m 644 files/audi-mmi-update.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-update.service"
install -m 644 files/audi-mmi-update.timer "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-update.timer"

install -m 644 files/99-carlinkit.rules "${ROOTFS_DIR}/etc/udev/rules.d/99-carlinkit.rules"

# react-carplay AppImage is fetched here (on the build machine, which has
# internet) and baked directly into the image, so the finished Pi is fully
# CarPlay-ready offline from the very first boot - no network dependency
# at runtime for the core kiosk functionality.
CARPLAY_VERSION="4.0.5"
CARPLAY_URL="https://github.com/rhysmorgan134/react-carplay/releases/download/v${CARPLAY_VERSION}/react-carplay-${CARPLAY_VERSION}-arm64.AppImage"
CARPLAY_DEST="${ROOTFS_DIR}/opt/audi-mmi/carplay/react-carplay-${CARPLAY_VERSION}-arm64.AppImage"
if [ ! -f "$CARPLAY_DEST" ]; then
  curl -L -o "$CARPLAY_DEST" "$CARPLAY_URL"
fi
chmod 755 "$CARPLAY_DEST"

on_chroot << EOF
systemctl enable seatd.service
systemctl enable audi-mmi-kiosk.service
systemctl enable audi-mmi-home-watcher.service
systemctl enable audi-mmi-firstboot.service
systemctl enable audi-mmi-update.timer
systemctl disable bluetooth.service || true
EOF
