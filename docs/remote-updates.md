# Flashen und Fernupdates

## Einmalige Installation auf der SD-Karte

1. Das veröffentlichte Audi-MMI-Image im Raspberry Pi Imager als eigenes Image wählen.
2. Im Imager Benutzer, WLAN, Zeitzone und SSH mit öffentlichem Schlüssel setzen.
3. Image auf die SD-Karte schreiben und den Pi einmal im Heimnetz starten.
4. Display, Touch, Ton und CarPlay prüfen.
5. Tailscale einmalig auf dem Pi installieren und mit demselben Tailnet wie den
   Entwicklungs-Mac verbinden. Der Gerätename soll `audi-mmi-pi` sein.

Tailscale stellt nur den privaten Netzwerkweg her. Es wird kein SSH-Port am
Router und kein Port im öffentlichen Internet geöffnet. Der Pi muss für ein
Update trotzdem online sein, etwa über Heim-WLAN, Telefon-Hotspot oder einen
späteren LTE-Router.

## Normale MMI-Updates

Oberfläche, Kies-Drive-Integration, Dienste und Konfiguration werden vom Mac
aus eingespielt:

```bash
MMI_PI_HOST=audi-mmi-pi ./scripts/deploy.sh
```

Mit MagicDNS kann `audi-mmi-pi` unabhängig davon gleich bleiben, ob das Auto
gerade im Heim-WLAN oder am Telefon-Hotspot hängt. Das Skript prüft die Dateien
vor der Installation, sichert die vorhandene Version, startet die MMI-Dienste
neu und kontrolliert deren Status. Schlägt ein Schritt fehl, wird die vorherige
Version wiederhergestellt. Die letzten drei Sicherungen bleiben auf dem Pi.

Ein solches Update benötigt normalerweise kein neues SD-Karten-Image und
keinen Ausbau des Pi. Der Bildschirm startet während des Updates einmal neu.
Updates deshalb nur im Stand durchführen.

## Wann erneut geflasht wird

Ein neues Image ist nur nötig bei Änderungen an Partitionierung oder
Basissystem, bei einer defekten SD-Karte oder für eine vollständige saubere
Neuinstallation. Normale Änderungen an MMI, Kies Drive, CAN-Auswertung und
CarPlay werden per Fernupdate verteilt.

## Betriebssystem-Updates

Debian-Pakete werden getrennt von der MMI-Anwendung aktualisiert. Diese
Updates werden bewusst manuell ausgeführt und danach getestet; automatische
Systemupdates im Fahrzeug könnten sonst einen Neustart oder eine unerwartete
Inkompatibilität verursachen.
