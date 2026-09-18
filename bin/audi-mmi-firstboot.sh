#!/bin/bash
# Runs once on first boot after flashing. The actual login user/name is only
# decided at flash time (Raspberry Pi Imager's OS customization), so this
# discovers whoever ended up as UID 1000 and grants them what the kiosk
# needs, instead of hardcoding a username into the image.
set -e

MARKER=/etc/audi-mmi-firstboot-done
[ -f "$MARKER" ] && exit 0

USERNAME="$(getent passwd 1000 | cut -d: -f1)"
if [ -z "$USERNAME" ]; then
  echo "audi-mmi-firstboot: no UID 1000 user found yet, retrying next boot"
  exit 1
fi

usermod -aG input,video,render,plugdev "$USERNAME"

SUDOERS_FILE=/etc/sudoers.d/010-audi-mmi-nopasswd
echo "$USERNAME ALL=(ALL) NOPASSWD: ALL" > "$SUDOERS_FILE"
chmod 0440 "$SUDOERS_FILE"
visudo -cf "$SUDOERS_FILE"

touch "$MARKER"
