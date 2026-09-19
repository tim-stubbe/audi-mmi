# Audi MMI – Raspberry Pi Infotainment & CarPlay

Selbstgebautes Infotainment-/CarPlay-System für einen Audi A4 B8 Avant (EZ 11/2011)
auf Basis eines Raspberry Pi 5 (4 GB), eines Waveshare 10.4HP-CAPQLED-Touchdisplays
und eines Carlinkit CPC200-CCPA/CCPM CarPlay-Dongles.

## Hardware

- Raspberry Pi 5 (4 GB) mit Active Cooler, eigenes 64-bit-Raspberry-Pi-OS-Image (Debian 13 "trixie")
- Waveshare 10.4HP-CAPQLED, 1600×720 @ ~59 Hz, HDMI + USB-C Touch
- Carlinkit CPC200-CCPA/CCPM (kabelgebunden/kabellos CarPlay)
- Audi Music Interface (AMI) auf USB bzw. 3,5mm AUX für späteren Ton

## Installation

Fertiges Image unter den [Releases](../../releases) dieses Repos, mit
Raspberry Pi Imager als "Custom Image" flashen. Benutzername/WLAN/Passwort
wie gewohnt über die Imager-Erweiterten-Optionen setzen - das Image selbst
enthält keine Zugangsdaten. Details zum Eigenbau des Images:
`docs/os-image-build.md`.

## Architektur

```
systemd: audi-mmi-kiosk.service   -> bin/kiosk-runner.sh
                                      - startet 'cage' (minimaler Wayland-Kiosk-Compositor)
                                      - abwechselnd mit native-launcher/launcher.py (GTK3/Python)
                                        oder dem react-carplay-AppImage
                                      - cage zeigt pro Sitzung nur eine App -> Wechsel = cage
                                        neu starten (dauert < 1s, kein zweiter Prozess parallel)

systemd: audi-mmi-home-watcher.service -> bin/touch-home-watcher.py
                                      - liest Touch-Events direkt vom Kernel (evdev)
                                      - Long-Press oben links (>=1.2s) -> laufendes cage beenden,
                                        kiosk-runner.sh springt automatisch zurück zum Launcher
                                      - funktioniert auch, wenn CarPlay im Vordergrund ist

systemd: audi-mmi-firstboot.service -> bin/audi-mmi-firstboot.sh
                                      - einmalig beim ersten Boot: findet den per Imager
                                        angelegten Benutzer (UID 1000) und vergibt
                                        passwortloses sudo + Gruppenrechte (input/video/etc.)
```

Der Launcher ist bewusst eine native GTK3/Python-App statt Electron/Chromium
(ursprünglicher Ansatz). Das hält Startzeit und Grundlast niedrig und lässt
dem CarPlay-Prozess, CAN-Auswertung und späteren Fahrzeugseiten genügend Reserve.
react-carplay wird als offizielles, vorgefertigtes AppImage genutzt (kein
Quellcode-Build auf dem Pi) und beim Bau des OS-Images direkt einbelackt,
damit das System auch ganz ohne Internetzugang CarPlay-bereit ist.

## Verzeichnisse

- `native-launcher/` – GTK3/Python-Kiosk-Oberfläche
- `bin/` – Hilfsskripte (Kiosk-Runner, Touch-Gesten-Watcher, Erstboot-Setup)
- `systemd/` – systemd-Units für Autostart
- `pi-gen-stage/` – eigene pi-gen-Stage zum Bauen des kompletten OS-Images
- `carplay/` – udev-Regel für den Carlinkit-Dongle
- `backups/pi/<datum>/` – Originalkonfigurationen (aus der Zeit vor dem Custom-Image)
- `docs/` – Setup-Notizen, offene Punkte, Wiederherstellungsanleitung

## Status (Stand 2026-09-18)

**Erledigt:**
- Eigenes 64-bit-OS-Image per pi-gen (kein Desktop, kein Chrome, minimaler
  Fußabdruck), als GitHub-Release veröffentlicht
- Native GTK3-Launcher-UI (schwarz, Icon-Leiste + Kachel-Grid im MMI-Stil)
- react-carplay v4.0.5 (arm64 AppImage) direkt ins Image einbelackt
- Umschaltung Launcher <-> CarPlay über cage-Neustart, Touch-Geste zum Zurückkehren
- Passwortlose-sudo-Vergabe beim Erstboot, unabhängig vom gewählten Benutzernamen
- Vorschau der UI ganz ohne Pi-Hardware möglich (Docker-Container mit
  Xvfb+VNC, siehe `docs/os-image-build.md`)
- Bestandsaufnahme der ursprünglichen Pi-OS-Installation (Display, Touch,
  Netzwerk, Audio-Pfad) – siehe `docs/display-notes.md`, `docs/audio-notes.md`

**Noch offen:**
- Neues Image auf der SD-Karte testen (physischer Neu-Flash steht aus)
- Carlinkit-Dongle ist noch nicht gekauft/angeschlossen – USB-Erkennung und
  echtes CarPlay-Pairing (kabelgebunden/kabellos) stehen noch aus
- Mikrofonlösung noch offen (Audi-Originalmikrofon ist NICHT automatisch am Pi verfügbar)
- Fahrzeugdaten-Seite (CAN, nur lesend) – noch nicht begonnen, siehe `docs/vehicle-data-plan.md`
- Finale Performance-/Boot-Zeit-Messung mit laufendem CarPlay auf dem Pi 5
- Icon-Feinschliff (aktuelles Einstellungen-Icon sieht eher nach Sonne als Zahnrad aus)

## Zugriff

```
ssh audi-mmi-pi   # Alias in ~/.ssh/config, Key-Auth, kein Passwort nötig
```

Aktuelle Pi-IP hängt vom Netzwerk ab (Hotspot/Heimnetz) – siehe `docs/network-notes.md`.
