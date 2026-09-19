# Fahrzeugdaten und CAN-Anbindung

Ziel ist eine dauerhaft eingebaute, elektrisch getrennte CAN-Anbindung für den
Audi A4 B8. Die erste Ausbaustufe liest ausschließlich mit. Sie liefert der
MMI-Oberfläche Bordspannung, Drehzahl, Geschwindigkeit, Kühlmitteltemperatur,
Verbrauch, Tür-/Klappenstatus und – soweit der jeweilige Bus sie bereitstellt –
Außentemperatur und Reichweite.

## Festgelegte Hardware

- Raspberry Pi 5 mit 4 GB RAM, bereits bestücktem 40-Pin-Header und Active Cooler
- Waveshare **2-CH CAN HAT+** (MCP2515, galvanische Trennung, TVS-Schutz,
  7–36-V-Eingang). Nur ein Kanal wird zunächst verwendet; der zweite bleibt für
  einen späteren Infotainment-/Komfort-CAN frei.
- Abgesicherter, rückrüstbarer Abgriff: zunächst OBD-II-Verlängerung/Y-Kabel;
  für den endgültigen unsichtbaren Einbau später ein fahrzeugspezifischer
  Zwischenadapter am Gateway/MMI-Kabelbaum.
- CAN-H, CAN-L und Masse. Der 120-Ohm-Abschluss auf dem HAT bleibt **aus**, weil
  der Fahrzeugbus bereits an seinen Enden terminiert ist.
- Eigene 3-A-Sicherung nahe dem 12-V-Abgriff. Der Pi 5 benötigt unter Last
  deutlich mehr Leistung als der ursprünglich vorgesehene Zero 2 W.
- Zündungs-/ACC-Erkennung plus verzögerte, saubere Abschaltung. Der Weitbereichs-
  eingang des CAN-HATs ersetzt diese Abschaltlogik nicht. Dauerplus ohne
  Abschaltung würde Batterie und SD-Karte unnötig belasten.

## Einbau- und Testreihenfolge

1. HAT zunächst am Tisch mit SocketCAN und `can-utils` prüfen.
2. Im Auto ausschließlich passiv und im Listen-Only-Modus starten.
3. Am OBD-Port zuerst Diagnose-CAN testen (typisch Pins 6/14, Masse 4/5). Die
   Belegung wird vor Anschluss am konkreten Auto gemessen bzw. aus dem
   Stromlaufplan bestätigt.
4. Busgeschwindigkeit bestimmen, Nachrichten protokollieren und Zustandswechsel
   kontrolliert zuordnen (Tür, Licht, Zündung usw.).
5. Erst nach erfolgreichem Read-only-Test den unsichtbaren Zwischenadapter am
   passenden Audi-Bus bauen. Kabelbaum nicht auftrennen.
6. Schreibzugriffe, UDS-Anpassungen und Codierungen bleiben gesperrt, bis
   Steuergeräte, Adressen, Sicherungskopien und Rückfallweg eindeutig sind.

## Stromversorgung des Pi 5

Der 7–36-V-Eingang des 2-CH CAN HAT+ darf den Pi über den 40-Pin-Anschluss
versorgen; Waveshare führt den HAT ausdrücklich als Pi-5-kompatibel. Die
Versorgung kommt für den endgültigen Einbau von einem separat abgesicherten
12-V-Abgriff und nicht dauerhaft aus Pin 16 der Diagnosebuchse. Zwischen
Abgriff und HAT gehört eine Automotive-Abschaltsteuerung: ACC wird als Signal
erfasst, das Betriebssystem fährt zuerst sauber herunter und erst danach wird
die Versorgung zeitverzögert getrennt.

## Originalradio

Der originale Audi-Tuner und das MMI-Steuergerät bleiben angeschlossen. Damit
bleiben FM/AM bzw. vorhandenes DAB und die Fahrzeug-Audiohardware erhalten. Der
Pi ersetzt die sichtbare Oberfläche, nicht den Radioempfänger. Für eine
vollständige Senderliste und Senderwahl auf dem neuen Display muss anschließend
die Kommunikation zwischen MMI, Radio und Bedieneinheit gelesen und abgebildet
werden. Bis dahin kann der zuletzt gewählte Sender weiterlaufen; vorhandene
Originaltasten funktionieren nur, soweit ihre ursprüngliche Hardware weiterhin
angeschlossen bleibt.
