# Audio

Der Pi Zero 2 W hat **keinen eingebauten 3,5mm-Audioausgang** (nur Pi 3B/4/400
haben den analogen Klinkenausgang). Einzige ALSA-Karte ist `vc4-hdmi`
(HDMI-Audio). Der Ton läuft daher:

```
Pi (HDMI-Audio, PipeWire-Sink "Built-in Audio Digital Stereo (HDMI)")
  -> HDMI-Kabel -> Waveshare 10.4HP-CAPQLED (hat eine eigene 3,5mm-Buchse
     am Treiberboard, extrahiert den eingebetteten HDMI-Ton)
  -> 3,5mm-Kabel -> AMI-AUX -> Audi MMI
```

- HDMI-Sink ist bereits der PipeWire-Standardausgang (kein Fallback auf
  einen X11-Bildschirm-Sprecher o.ä. nötig).
- Lautstärke auf 85% gesetzt (`wpctl set-volume <sink-id> 0.85`), Feinjustage
  erst sinnvoll mit realem CarPlay-Ton bzw. am AMI-AUX-Eingang.
- Physischer Test (Ton am Display hörbar?) steht noch aus, da wir beim Test
  nicht am Gerät waren – vor dem Einbau unbedingt nachholen.
