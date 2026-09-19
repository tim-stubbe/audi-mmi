FROM debian:trixie-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    xvfb x11vnc dbus-x11 matchbox-window-manager \
    && rm -rf /var/lib/apt/lists/*

COPY native-launcher/launcher.py /opt/audi-mmi/native-launcher/launcher.py
COPY native-launcher/assets/alps-background.png /opt/audi-mmi/native-launcher/assets/alps-background.png
COPY preview/entrypoint.sh /entrypoint.sh

RUN chmod 755 /entrypoint.sh

EXPOSE 5900
ENTRYPOINT ["/entrypoint.sh"]
