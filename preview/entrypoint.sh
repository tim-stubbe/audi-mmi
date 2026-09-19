#!/bin/sh
set -eu

Xvfb :99 -screen 0 1600x720x24 &
sleep 1
export DISPLAY=:99
matchbox-window-manager -use_titlebar no &
sleep 1
x11vnc -display :99 -forever -passwd "${VNC_PASSWORD:-audimmi}" \
  -shared -rfbport 5900 -bg -o /var/log/x11vnc.log
exec python3 /opt/audi-mmi/native-launcher/launcher.py
