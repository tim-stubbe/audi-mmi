# Flashen und Updates über den iPhone-Hotspot

## Einmalige Installation auf der SD-Karte

1. Das veröffentlichte Audi-MMI-Image im Raspberry Pi Imager als eigenes Image wählen.
2. Im Imager Benutzer, Zeitzone und SSH setzen.
3. Den iPhone-Hotspot als gespeichertes WLAN eintragen.
4. Image auf die SD-Karte schreiben und den Pi einmal starten.
5. Display, Touch, Ton und CarPlay prüfen.

Auf dem Pi wird kein Tailscale installiert. Der iPhone-Hotspot liefert nur die
Internetverbindung. Ein öffentlicher SSH-Port wird ebenfalls nicht benötigt.

## Automatische Abrufrichtung

Der Pi kann hinter dem Mobilfunknetz nicht zuverlässig von außen angesprochen
werden. Deshalb ruft er Updates selbst über HTTPS aus dem öffentlichen
GitHub-Repository ab. Zwei Minuten nach jedem Start prüft er das neueste
Release auf die Datei `audi-mmi-update.tar.gz`.

Ist kein solches geprüftes Anwendungspaket vorhanden, passiert nichts. Ist eine
neuere Version vorhanden, werden Download und Prüfsumme kontrolliert, die alte
Installation gesichert und das Update eingespielt. Danach starten die beiden
MMI-Dienste neu. Bei einem Fehler stellt der Updater die vorherige Version
wieder her. Die letzten drei Sicherungen bleiben lokal erhalten.

Damit das funktioniert, muss der iPhone-Hotspot beim Start des Pi erreichbar
sein. Wird der Hotspot erst später eingeschaltet, genügt ein Neustart des MMI.

## Update veröffentlichen

Nach dem Test in der TrueNAS-Vorschau wird zunächst das kleine Anwendungspaket
gebaut:

```bash
./scripts/build-update-bundle.sh
```

Die erzeugte Datei `dist/audi-mmi-update.tar.gz` wird nur an ein als stabil
freigegebenes GitHub-Release angehängt. Der Pi installiert keine beliebigen
Commits und keine Vorschauversionen.

## Lokales Wartungsupdate

Wenn Mac und Pi gleichzeitig mit demselben iPhone-Hotspot verbunden sind, kann
das bestehende SSH-Update weiterhin als Wartungsweg verwendet werden:

```bash
MMI_PI_HOST=172.20.10.2 ./scripts/deploy.sh
```

## Wann erneut geflasht wird

Ein neues Image ist nur bei Änderungen an Partitionierung oder Basissystem,
bei einer defekten SD-Karte oder für eine vollständige Neuinstallation nötig.
Oberfläche, Kies Drive, CAN-Auswertung und normale CarPlay-Anpassungen kommen
über das kleine Anwendungspaket.
