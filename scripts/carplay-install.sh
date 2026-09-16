#!/usr/bin/env bash
# Installs the official react-carplay AppImage (v4.0.5, arm64) on the Pi.
# Source: https://github.com/rhysmorgan134/react-carplay/releases
set -euo pipefail

HOST="audi-mmi-pi"
VERSION="4.0.5"
URL="https://github.com/rhysmorgan134/react-carplay/releases/download/v${VERSION}/react-carplay-${VERSION}-arm64.AppImage"

ssh "$HOST" "mkdir -p /opt/audi-mmi/carplay && \
  curl -L -o /opt/audi-mmi/carplay/react-carplay-${VERSION}-arm64.AppImage '$URL' && \
  chmod +x /opt/audi-mmi/carplay/react-carplay-${VERSION}-arm64.AppImage"

echo "==> react-carplay ${VERSION} installiert unter /opt/audi-mmi/carplay/"
echo "==> udev-Regel fuer den Carlinkit-Dongle per deploy.sh einspielen (falls noch nicht geschehen)"
