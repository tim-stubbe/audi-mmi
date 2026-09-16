# Netzwerk

- WLAN-Regulatory-Domain ist auf `CH` (Schweiz) gesetzt – korrekt, da dauerhafter
  Umzug in die Schweiz erfolgt ist. Keine Änderung nötig.
- Es gab zwei gespeicherte NetworkManager-Profile fürs Heimnetz, eines mit
  Schreibfehler in der SSID (`Villakunterbunt 2` statt `VillaKunterbunt 2`) –
  das fehlerhafte Profil (`netplan-wlan0-Villakunterbunt 2`) wurde gelöscht.
  Das korrekte Profil `VillaKunterbunt 2` bleibt bestehen und sollte sich
  automatisch verbinden, sobald der Pi in Reichweite dieses Netzes ist.
- Für die Ersteinrichtung wurde der Pi vorübergehend über den mobilen Hotspot
  des Telefons verbunden (`iPhone von Tim`, 172.20.10.0/28).
- SSH-Alias `audi-mmi-pi` in `~/.ssh/config` auf dem Mac zeigt aktuell auf die
  Hotspot-IP `172.20.10.2` – diese ändert sich, sobald der Pi in einem anderen
  Netz landet. Vor dem nächsten Zugriff ggf. IP neu ermitteln (ARP-Scan) und
  die `HostName`-Zeile in `~/.ssh/config` aktualisieren.
