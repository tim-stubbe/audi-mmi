# Audi MMI – Raspberry Pi Infotainment & CarPlay

Selbstgebautes Infotainment-/CarPlay-System für einen Audi A4 B8 Avant (EZ 11/2011)
auf Basis eines Raspberry Pi Zero 2 W, eines Waveshare 10.4HP-CAPQLED-Touchdisplays
und eines Carlinkit CPC200-CCPA/CCPM CarPlay-Dongles.

## Hardware

- Raspberry Pi Zero 2 W (512MB RAM), Raspberry Pi OS 64-bit (Debian 13 "trixie")
- Waveshare 10.4HP-CAPQLED, 1600×720 @ ~59 Hz, HDMI + USB-C Touch
- Carlinkit CPC200-CCPA/CCPM (kabelgebunden/kabellos CarPlay)
- Audi Music Interface (AMI) auf USB bzw. 3,5mm AUX für späteren Ton

## Architektur

```
systemd: audi-mmi-ui.service          -> launcher/server.py (Python, stdlib-only)
                                          - serviert launcher/index.html (Kiosk-UI)
                                          - startet Chromium im Kiosk-Modus (Wayland/labwc)
                                          - schaltet auf Tastendruck auf CarPlay AppImage um

systemd: audi-mmi-home-watcher.service -> bin/touch-home-watcher.py
                                          - liest Touch-Events direkt vom Kernel (evdev)
                                          - Long-Press oben links (>=1.2s) -> zurück zum Launcher
                                          - funktioniert auch, wenn CarPlay im Vordergrund ist
```

Der Launcher läuft bewusst NICHT als Electron-App, sondern als minimaler Python-
HTTP-Server + statisches HTML/CSS/JS, um auf dem RAM-knappen Pi Zero 2 W
(512MB) Ressourcen für CarPlay selbst freizuhalten. react-carplay wird als
offizielles, vorgefertigtes AppImage (kein Quellcode-Build auf dem Pi) genutzt.

## Verzeichnisse

- `launcher/` – Kiosk-Oberfläche (HTML/CSS/JS) + Backend (server.py)
- `bin/` – Hilfsskripte (Touch-Gesten-Watcher)
- `systemd/` – systemd-Units für Autostart
- `carplay/` – udev-Regel für den Carlinkit-Dongle
- `backups/pi/<datum>/` – Originalkonfigurationen vor Änderungen
- `docs/` – Setup-Notizen, offene Punkte, Wiederherstellungsanleitung

## Status (Stand 2026-09-16)

**Erledigt:**
- SSH-Zugriff per Schlüssel eingerichtet, passwortloses sudo für Ersteinrichtung
- Bestandsaufnahme: Modell, OS, RAM/Swap (zram, bereits optimal), Temperatur, USB, Display, Touch, Netzwerk
- Display läuft nativ mit 1600×720 (Panel-EDID liefert ~59,05 Hz statt nominell 60 Hz –
  technisch bedingt, visuell irrelevant, siehe `docs/display-notes.md`)
- Touch korrekt erkannt (libinput, Identity-Kalibrierung, keine Achsenvertauschung)
- Defektes WLAN-Profil (SSID-Schreibfehler) entfernt
- Kiosk-Launcher-UI (schwarz, große Kacheln: CarPlay/Fahrzeugdaten/Einstellungen/Herunterfahren)
- react-carplay v4.0.5 (arm64 AppImage, offizielles GitHub-Release) installiert
- Umschaltung Launcher <-> CarPlay getestet (API + Touch-Geste)
- Autostart nach Kaltstart verifiziert

**Noch offen:**
- Carlinkit-Dongle ist noch nicht gekauft/angeschlossen – USB-Erkennung und
  echtes CarPlay-Pairing (kabelgebunden/kabellos) stehen noch aus
- Audioausgang (HDMI/3,5mm -> AMI-AUX) noch nicht konfiguriert
- Mikrofonlösung noch offen (Audi-Originalmikrofon ist NICHT automatisch am Pi verfügbar)
- Fahrzeugdaten-Seite (CAN, nur lesend) – noch nicht begonnen, siehe `docs/vehicle-data-plan.md`
- Dienste-Optimierung (bluetooth/rpcbind/nfs-blkmap/packagekit prüfen und ggf. deaktivieren)
- Finale Performance-/Boot-Zeit-Messung mit laufendem CarPlay (Video-Decoding ist der
  wahrscheinliche Engpass auf dem Zero 2 W)
- Passwort auf dem Pi ändern (aktuell ein Test-Passwort, siehe `docs/security-notes.md`)

## Zugriff

```
ssh audi-mmi-pi   # Alias in ~/.ssh/config, Key-Auth, kein Passwort nötig
```

Aktuelle Pi-IP hängt vom Netzwerk ab (Hotspot/Heimnetz) – siehe `docs/network-notes.md`.
