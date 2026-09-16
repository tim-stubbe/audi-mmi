# Fahrzeugdaten-Seite (Plan, noch nicht umgesetzt)

Ziel: eigene Seite im Launcher mit rein lesenden CAN-/Diagnosedaten:
Bordspannung, Batterie-Ladezustand (Schätzung), Kühlmitteltemperatur,
Drehzahl, Geschwindigkeit, Verbrauch.

## Reihenfolge (verbindlich, bevor irgendetwas geschrieben/codiert wird)

1. Alle relevanten Steuergeräte des A4 B8 (Bj. 11/2011, wahrscheinlich MJ2012)
   identifizieren (Motorsteuergerät, Kombiinstrument, ggf. Gateway).
2. Originalwerte/-konfiguration sichern, bevor irgendein Diagnose-Tool aktiv
   etwas anfragt, das potenziell Zustände verändert.
3. Ausschließlich passives Mitlesen des CAN-Bus (Read-Only-Adapter, z.B. ein
   USB-CAN-Interface mit dediziertem Empfangsfilter, keine UDS-Schreibzugriffe,
   kein Flashen, kein Codieren).
4. Erst danach: Mapping der benötigten PIDs/CAN-IDs für die gewünschten Werte,
   auf Basis der A4-B8/MLB-Plattform-Dokumentation (nicht raten).

## Offene Fragen für die Umsetzung

- Welcher CAN-Bus ist am Pi überhaupt zugänglich (Comfort-CAN/Infotainment-CAN
  vs. Antriebs-CAN) und wie wird sicher (galvanisch getrennt, read-only)
  angeschlossen? Das Original-MMI und dessen Kabelbaum dürfen dabei nicht
  verändert werden.
- Welche Hardware wird für den CAN-Zugriff verwendet (z.B. MCP2515-Modul,
  USB-CAN-Adapter)? Noch nicht beschafft.
- Kombiinstrument des B8 liefert viele Werte bereits über den Comfort-CAN;
  Motorwerte (Drehzahl, Kühlmitteltemp, Verbrauch) eher über den Antriebs-CAN
  bzw. per OBD-Port (PIDs zumindest teilweise standardisiert nach OBD-2).

Dieser Plan wird erst konkretisiert, sobald CAN-Hardware vorhanden ist. Bis
dahin bleibt der Tab "Fahrzeugdaten" im Launcher ein Platzhalter.
