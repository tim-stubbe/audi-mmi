# Display: Waveshare 10.4HP-CAPQLED

Das Display liefert über sein eigenes EDID (per DDC) nur einen nativen
1600×720-Modus mit **59,05 Hz**, nicht exakt 60,00 Hz. Das ist die tatsächliche
Panel-Taktung dieses Controllers, kein Erkennungsfehler.

Die von Waveshare dokumentierten `hdmi_group=2 hdmi_mode=87 hdmi_timings=...`-Werte
(für exakt 60,00 Hz) wurden getestet, hatten aber unter dem aktuellen
`vc4-kms-v3d`-KMS-Treiber **keine Wirkung**: Der Treiber bevorzugt das reale
EDID des angeschlossenen Displays gegenüber den manuellen Firmware-Timings.
Das bestätigt `wlr-randr`, das keinen 60,00-Hz-Eintrag für 1600×720 listet.

Um exakt 60,00 Hz zu erzwingen, müsste zusätzlich `hdmi_ignore_edid` gesetzt
werden (das reale EDID des Displays wird dann komplett ignoriert). Das kann
Nebenwirkungen auf Audio-/Geräteerkennung haben und wurde bewusst NICHT
gesetzt, da 59,05 Hz visuell nicht von 60 Hz unterscheidbar ist und keine
Auswirkung auf Touch oder CarPlay hat.

`/boot/firmware/config.txt` ist daher unverändert gegenüber der
Werksinstallation (siehe `backups/pi/20260916/boot_firmware/config.txt.orig`).
