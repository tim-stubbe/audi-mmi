# Eigenes OS-Image (pi-gen)

Nach dem RAM-Problem mit dem Chromium-Kiosk (siehe Git-Historie) wurde die
komplette Launcher-UI auf eine native GTK3/Python-Anwendung umgestellt und
zusätzlich ein eigenes, schlankes Raspberry-Pi-OS-Image gebaut - ohne
Desktop, ohne Chrome, nur `cage` (Wayland-Kiosk-Compositor) + unsere App.

## Warum kein Docker auf dem Mac

`pi-gen`s Bootstrap-Prozess (`setarch linux32`) scheitert in Docker Desktop
für macOS, weil dessen VM diesen Syscall blockiert (bekannte Einschränkung).
Der Build läuft stattdessen in einer **Multipass-Ubuntu-VM** (echter Linux-
Kernel), nicht in Docker.

## Wichtig: den `arm64`-Branch von pi-gen verwenden

Der `master`-Branch von pi-gen baut standardmäßig **32-bit (armhf)**-Images.
Unser CarPlay-AppImage ist aber explizit `arm64`. Für ein 64-bit-Image muss
der `arm64`-Branch ausgecheckt werden:

```
git clone --branch arm64 https://github.com/RPi-Distro/pi-gen.git
```

Auf einem arm64-Build-Host (z.B. Apple-Silicon-Mac via Multipass) läuft das
außerdem **nativ ohne QEMU-Emulation** - deutlich schneller und robuster als
der `master`-Branch, der für armhf-Ziele immer QEMU-Übersetzung braucht.

## Build-Schritte (Kurzfassung)

```bash
multipass launch --name pigen-builder --cpus 4 --memory 4G --disk 25G 22.04
multipass exec pigen-builder -- bash -c "sudo apt-get update && sudo apt-get install -y \
  coreutils quilt parted qemu-user-binfmt debootstrap zerofree zip dosfstools \
  e2fsprogs libarchive-tools libcap2-bin grep rsync xz-utils file git curl bc \
  gpg pigz xxd arch-test bmap-tools kmod"

multipass transfer -r pi-gen-arm64 pigen-builder:/home/ubuntu/
# pi-gen-stage/ (aus diesem Repo) nach pi-gen-arm64/stage-audi-mmi kopieren,
# config nach pi-gen-arm64/config, dann:
multipass exec pigen-builder -- bash -c "rm -f /home/ubuntu/pi-gen-arm64/stage2/EXPORT_IMAGE
  cd /home/ubuntu/pi-gen-arm64 && sudo ./build.sh"

multipass transfer pigen-builder:/home/ubuntu/pi-gen-arm64/deploy/image_*.img.xz .
```

Das fertige Image landet als GitHub-Release-Asset (zu groß fürs normale Git),
siehe Releases dieses Repos.

## Architektur des Images

- Basis: Raspberry Pi OS Lite (stage0-2), kein Desktop (stage3-5 übersprungen)
- Eigene Stage `stage-audi-mmi`: installiert `cage`, `seatd`, GTK3/PyGObject,
  `python3-evdev`, PipeWire/WirePlumber, `fuse3`/`libfuse2t64`
- react-carplay-AppImage wird beim Bau direkt heruntergeladen und einbelackt
  -> das fertige Image ist ab dem ersten Boot CarPlay-bereit, auch offline
- `audi-mmi-kiosk.service`: startet `kiosk-runner.sh`, das `cage` abwechselnd
  mit unserer `native-launcher/launcher.py` oder dem CarPlay-AppImage startet
  (cage kann pro Sitzung nur eine App zeigen - Wechsel = cage neu starten)
- `audi-mmi-home-watcher.service`: liest Touch-Events direkt vom Kernel,
  Long-Press oben links killt den laufenden `cage`-Prozess -> zurück zum Launcher
- `audi-mmi-firstboot.service`: findet beim ersten Boot heraus, welcher
  Benutzername tatsächlich angelegt wurde (Raspberry Pi Imager legt den erst
  beim Flashen fest) und vergibt darauf passwortloses sudo + Gruppenrechte

## Benutzername/WLAN/Passwort

Werden weiterhin ganz normal über Raspberry Pi Imager ("Erweiterte Optionen"
bzw. Zahnrad-Symbol) beim Flashen gesetzt, wie bei jedem Standard-Image auch.
Das Image selbst enthält keine Zugangsdaten.

## Vorschau ohne Flashen

Da `native-launcher/launcher.py` reines Python/GTK3 ohne Pi-spezifische
Abhängigkeiten ist, lässt sie sich in jeder Linux-Umgebung mit GTK3
anschauen - ganz ohne Raspberry-Pi-Hardware-Emulation. Ein Docker-Container
mit `Xvfb` + `matchbox-window-manager` + `x11vnc` reicht für eine exakte
1600x720-Vorschau per VNC. Praktisch für schnelles Feedback, bevor man die
SD-Karte neu flasht.

Die Vorschau auf dem TrueNAS-Testserver wird reproduzierbar aktualisiert mit:

```bash
./preview/deploy-truenas.sh
```

Der Container ist nur die virtuelle Anzeige für schnelle Design- und
Bedienungstests. Das Fahrzeug verwendet weiterhin das eigene schlanke
Raspberry-Pi-OS-Image ohne Desktop und ohne Ubuntu.
