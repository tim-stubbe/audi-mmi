# Sicherheitshinweise

- Der Pi-Benutzer `tim` hat aktuell **passwortloses sudo** (`/etc/sudoers.d/010-tim-nopasswd`),
  eingerichtet für die Ersteinrichtung per SSH. Vor dem Einbau ins Fahrzeug abwägen,
  ob das so bleiben soll oder auf ein normales sudo-Passwort zurückgestellt wird.
- Das Login-Passwort des Pi wurde vom Nutzer bewusst als einfaches Test-Passwort
  ("1234") gesetzt und sollte vor dem Einbau ins Auto geändert werden
  (`passwd` auf dem Pi).
- SSH-Zugriff vom Mac erfolgt über einen dedizierten Schlüssel
  (`~/.ssh/id_ed25519_audi_mmi`, nur für dieses Projekt), Passwort-Auth bleibt
  serverseitig aktiv (Standard von Raspberry Pi OS) – für den späteren
  Fahrzeugeinsatz ggf. `PasswordAuthentication no` in `/etc/ssh/sshd_config` setzen.
- Kein Passwort wurde in Dateien, Skripten oder diesem Repository gespeichert.
