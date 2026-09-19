# Hardware-Stückliste für den endgültigen Einbau

## Rechner und Anzeige

- Raspberry Pi 5, 1 GB RAM. Das ist für das schlanke Kiosk-Image ausreichend,
  weil Launcher und CarPlay abwechselnd statt parallel laufen. 2 GB bleiben eine
  Komfortoption; 4 GB bringen für diesen Einbau keinen praktischen Vorteil.
- Raspberry Pi Active Cooler
- vorhandenes Waveshare 10.4HP-CAPQLED (1600×720)
- vorhandener Micro-HDMI-auf-HDMI-Adapter; kein weiterer Adapter erforderlich
- vorhandene microSD-Karte mit dem eigenen Audi-MMI-Image

## CarPlay und Audio

- Carlinkit CPC200-CCPA oder CPC200-CCPM, ausdrücklich die Variante für ein
  Android-/Linux-Hostsystem
- AMI-auf-3,5-mm-AUX-Adapter
- 3,5-mm-Audiokabel vom Kopfhörerausgang des Displays zum AMI-AUX-Adapter
- Display-Touch per USB und Carlinkit direkt an zwei getrennten USB-Ports des Pi 5

## CAN

- Waveshare 2-CH CAN HAT+ (MCP2515/SN65HVD230, Plus-Version mit 7–36-V-Eingang)
- OBD-II-Y-Splitter für rückrüstbare Tests
- OBD-II-Stecker auf offene Leitungen für CAN-H, CAN-L und Masse
- Der 120-Ohm-Abschluss des HAT bleibt im Fahrzeug deaktiviert
- Kein zusätzlicher GPIO-Header: Beim Pi 5 ist der 40-Pin-Header bereits bestückt

## Dauerhafte Fahrzeugversorgung

- Mehrformat-Sicherungabgriff oder nach Kontrolle des Sicherungskastens der
  passende Audi-Sicherungsadapter
- 3-A-Kfz-Sicherung nahe am 12-V-Abgriff
- 16-AWG-Leitung für 12 V und Masse, Crimpverbinder und Ringkabelschuh für den
  vorhandenen Massepunkt
- Automotive-Controller mit ACC-Erkennung und verzögerter Lastabschaltung
- Stromversorgung über den 7–36-V-Eingang des CAN HAT+, nicht dauerhaft über
  den OBD-II-Pin 16

Der Shutdown-Controller ist ein Pflichtteil für den endgültigen Einbau. Ein
gewöhnlicher DC-Wandler, ein Motorregler oder ein einfaches Zeitrelais ohne
ACC-Signal an den Pi ersetzt die kontrollierte Abschaltung nicht.
