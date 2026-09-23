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
install -m 755 files/audi-mmi-updater.py "${ROOTFS_DIR}/opt/audi-mmi/bin/audi-mmi-updater.py"

install -m 644 files/audi-mmi-kiosk.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-kiosk.service"
install -m 644 files/audi-mmi-home-watcher.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-home-watcher.service"
install -m 644 files/audi-mmi-update.service "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-update.service"
install -m 644 files/audi-mmi-update.timer "${ROOTFS_DIR}/etc/systemd/system/audi-mmi-update.timer"

install -m 644 files/99-carlinkit.rules "${ROOTFS_DIR}/etc/udev/rules.d/99-carlinkit.rules"
printf '%s\n' 'os-2026-09-23' > "${ROOTFS_DIR}/opt/audi-mmi/VERSION"

# The appliance has a fixed, locked runtime account. It never asks for a
# username or password on first boot. Only the two commands used by the touch
# UI are available without a password.
on_chroot << EOF
usermod -aG input,video,render,plugdev,netdev "${FIRST_USER_NAME}"
passwd -l "${FIRST_USER_NAME}"
cat > /etc/sudoers.d/010-audi-mmi-ui <<'SUDOERS'
${FIRST_USER_NAME} ALL=(root) NOPASSWD: /usr/bin/nmcli, /usr/bin/systemctl poweroff, /usr/bin/systemctl reboot
SUDOERS
chmod 0440 /etc/sudoers.d/010-audi-mmi-ui
visudo -cf /etc/sudoers.d/010-audi-mmi-ui
EOF

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
systemctl disable audi-mmi-firstboot.service || true
systemctl enable audi-mmi-update.timer
systemctl disable bluetooth.service || true
EOF
