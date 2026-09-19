#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${MMI_PREVIEW_HOST:-truenas}"
REMOTE="/tmp/audi-mmi-preview-build"

tar -C "$ROOT" -czf - native-launcher preview | \
  ssh "$HOST" "rm -rf '$REMOTE' && mkdir -p '$REMOTE' && tar -xzf - -C '$REMOTE'"

ssh "$HOST" "cd '$REMOTE' && \
  sudo -n docker build -f preview/Dockerfile -t mmi-preview . && \
  sudo -n docker rm -f mmi-preview >/dev/null 2>&1 || true; \
  sudo -n docker run -d --name mmi-preview --restart unless-stopped \
    -p 5900:5900 mmi-preview"

echo "VNC preview available at ${HOST}:5900"
