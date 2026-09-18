# Dienste-Aufräumen (Ziel 14)

Geprüft und deaktiviert (jeweils Zweck vorher verifiziert):

| Dienst | Zweck | Warum deaktiviert |
|---|---|---|
| `bluetooth.service` | Pi-eigenes Bluetooth | react-carplay/Carlinkit-Dongle nutzt sein eigenes BT/WLAN für kabelloses CarPlay, nicht das des Pi. Kann bei Bedarf jederzeit reaktiviert werden (`sudo systemctl enable --now bluetooth`), falls sich das nach echtem Dongle-Test als falsch herausstellt. |
| `rpcbind.service` + `.socket` | NFS-Portmapper | Kein NFS im Einsatz. |
| `nfs-blkmap.service` | NFS Block-Layout-Mapping | Kein NFS im Einsatz. |
| `packagekit.service` | GUI-Paketverwaltung (Software-Updater) | Nicht nötig auf einem Appliance-Gerät; Updates laufen manuell per SSH/apt. |

**Nicht deaktiviert** (geprüft, aber benötigt):
- `avahi-daemon` – mDNS, nützlich für `audi-carplay.local`-Erreichbarkeit
- `cron` – Systemwartung (logrotate, man-db), geringer Ressourcenverbrauch
- `polkit` – von NetworkManager/systemd für Berechtigungen genutzt
- `accounts-daemon` – möglich von lightdm genutzt, minimaler Fußabdruck, Risiko > Nutzen

## Kiosk-Bereinigung (Ziel 12/13, kein systemd-Dienst)

`/etc/xdg/labwc/autostart` startete standardmäßig zusätzlich `pcmanfm-pi`
(Desktop-Icons) und `wf-panel-pi` (Taskleiste) – beide liefen unsichtbar unter
unserem Kiosk-Chromium und verbrauchten dauerhaft RAM. Beide Zeilen entfernt
(Backup: `backups/pi/20260916/etc-xdg-labwc-autostart.orig`).
Hinweis: labwc führt sowohl `/etc/xdg/labwc/autostart` als auch
`~/.config/labwc/autostart` additiv aus (nicht exklusiv) – Änderungen müssen
ggf. an beiden Stellen vorgenommen werden.

Effekt: nach Reboot ca. 30MB mehr verfügbarer RAM (195MB -> 227MB) und keine
sichtbare Linux-Desktop-Oberfläche mehr im Hintergrund.
