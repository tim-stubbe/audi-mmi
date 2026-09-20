#!/usr/bin/env python3
"""Native GTK kiosk launcher for the Audi MMI project.

Replaces the earlier Chromium-based launcher: runs as the single client
under the 'cage' Wayland kiosk compositor, using GTK3 directly instead of
a browser engine. On the Pi Zero 2 W (512MB RAM) this uses roughly
15-20MB instead of Chromium's 150-200MB, leaving far more headroom for
react-carplay when it is actually running.
"""

import os
import json
import subprocess
import time
from pathlib import Path

import math
import cairo

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Gdk  # noqa: E402


def draw_icon(name, color):
    """Renders one of our own simple line icons via Cairo, instead of
    relying on the host's icon theme (which may be minimal/absent, e.g.
    in a bare preview container) or inventing icon names that don't
    actually exist in any theme."""

    def _draw(widget, cr):
        size = min(widget.get_allocated_width(), widget.get_allocated_height()) or 48
        cr.set_line_width(size * 0.06)
        cr.set_source_rgb(*color)
        cr.set_line_cap(1)
        cr.set_line_join(1)
        s = size

        if name == "home":
            cr.move_to(s * 0.15, s * 0.55)
            cr.line_to(s * 0.5, s * 0.2)
            cr.line_to(s * 0.85, s * 0.55)
            cr.stroke()
            cr.rectangle(s * 0.28, s * 0.5, s * 0.44, s * 0.32)
            cr.stroke()
        elif name == "carplay":
            cx, cy = s * 0.5, s * 0.75
            for i, r in enumerate((0.2, 0.35, 0.5)):
                cr.arc(cx, cy, s * r, math.pi * 1.2, math.pi * 1.8)
                cr.stroke()
            cr.arc(cx, cy, s * 0.04, 0, 2 * math.pi)
            cr.fill()
        elif name == "vehicle":
            cr.move_to(s * 0.18, s * 0.62)
            cr.line_to(s * 0.28, s * 0.38)
            cr.curve_to(s * 0.32, s * 0.32, s * 0.68, s * 0.32, s * 0.72, s * 0.38)
            cr.line_to(s * 0.82, s * 0.62)
            cr.stroke()
            cr.move_to(s * 0.14, s * 0.62)
            cr.line_to(s * 0.86, s * 0.62)
            cr.stroke()
            for cx in (s * 0.3, s * 0.7):
                cr.arc(cx, s * 0.68, s * 0.08, 0, 2 * math.pi)
                cr.stroke()
        elif name == "settings":
            cx, cy = s * 0.5, s * 0.5
            cr.arc(cx, cy, s * 0.18, 0, 2 * math.pi)
            cr.stroke()
            for i in range(8):
                a = i * math.pi / 4
                x1, y1 = cx + math.cos(a) * s * 0.28, cy + math.sin(a) * s * 0.28
                x2, y2 = cx + math.cos(a) * s * 0.38, cy + math.sin(a) * s * 0.38
                cr.move_to(x1, y1)
                cr.line_to(x2, y2)
                cr.stroke()
        elif name == "shutdown":
            cx, cy = s * 0.5, s * 0.5
            cr.arc(cx, cy, s * 0.3, math.pi * 0.15, math.pi * 1.85)
            cr.stroke()
            cr.move_to(cx, cy - s * 0.38)
            cr.line_to(cx, cy - s * 0.05)
            cr.stroke()
        elif name == "radio":
            cr.rectangle(s * 0.18, s * 0.35, s * 0.64, s * 0.42)
            cr.stroke()
            cr.move_to(s * 0.35, s * 0.35)
            cr.line_to(s * 0.62, s * 0.15)
            cr.stroke()
            cr.arc(s * 0.35, s * 0.56, s * 0.08, 0, 2 * math.pi)
            cr.stroke()
        elif name == "media":
            cr.arc(s * 0.35, s * 0.68, s * 0.09, 0, 2 * math.pi)
            cr.stroke()
            cr.arc(s * 0.68, s * 0.6, s * 0.09, 0, 2 * math.pi)
            cr.stroke()
            cr.move_to(s * 0.44, s * 0.68)
            cr.line_to(s * 0.44, s * 0.25)
            cr.line_to(s * 0.77, s * 0.18)
            cr.line_to(s * 0.77, s * 0.6)
            cr.stroke()
        elif name == "phone":
            cr.move_to(s * 0.28, s * 0.2)
            cr.curve_to(s * 0.2, s * 0.3, s * 0.2, s * 0.5, s * 0.35, s * 0.65)
            cr.curve_to(s * 0.5, s * 0.8, s * 0.7, s * 0.8, s * 0.8, s * 0.72)
            cr.line_to(s * 0.68, s * 0.55)
            cr.line_to(s * 0.55, s * 0.6)
            cr.curve_to(s * 0.48, s * 0.52, s * 0.48, s * 0.52, s * 0.4, s * 0.45)
            cr.line_to(s * 0.45, s * 0.32)
            cr.line_to(s * 0.28, s * 0.2)
            cr.close_path()
            cr.stroke()
        elif name == "messages":
            cr.rectangle(s * 0.16, s * 0.28, s * 0.68, s * 0.46)
            cr.stroke()
            cr.move_to(s * 0.16, s * 0.3)
            cr.line_to(s * 0.5, s * 0.56)
            cr.line_to(s * 0.84, s * 0.3)
            cr.stroke()
        elif name == "navigation":
            cx, cy = s * 0.5, s * 0.55
            cr.move_to(cx, cy - s * 0.32)
            cr.line_to(cx + s * 0.2, cy + s * 0.22)
            cr.line_to(cx, cy + s * 0.1)
            cr.line_to(cx - s * 0.2, cy + s * 0.22)
            cr.close_path()
            cr.stroke()
        return False

    area = Gtk.DrawingArea()
    area.set_size_request(48, 48)
    area.connect("draw", _draw)
    return area

CARPLAY_APPIMAGE = "/opt/audi-mmi/carplay/react-carplay-4.0.5-arm64.AppImage"
KIES_DRIVE_EXECUTABLE = "/opt/audi-mmi/kies-drive/kies-drive"
CARLINKIT_VENDOR_ID = "1314"

CSS = b"""
window { background-color: #070708; }
.rail { background-color: #0b0b0c; border-right: 1px solid #29292d; }
.rail-btn { min-width: 68px; min-height: 68px; border-radius: 13px;
            background: transparent; color: #8b8b91; border: none; }
.rail-btn:hover, .rail-btn-active { background-color: #1a1a1d; color: #f2f2f3; }
.rail-btn-danger { color: #7a1620; }
.statusbar { border-bottom: 1px solid #29292d; }
.page-title { color: #f2f2f3; font-size: 29px; font-weight: 600; }
.page-subtitle { color: #8b8b91; font-size: 15px; }
.status-label { color: #8b8b91; font-size: 15px; }
.clock { color: #f2f2f3; font-size: 24px; font-weight: 600; }
.tile { background-color: #111113; border: 1px solid #29292d; border-radius: 12px; }
.tile:hover { background-color: #171719; border-color: #3a3a3f; }
.tile-label { color: #f2f2f3; font-size: 18px; font-weight: 600; }
.dot { min-width: 8px; min-height: 8px; border-radius: 4px; background-color: #7c7c80; }
.dot-online { background-color: #3ecf5f; }
"""


def read_volume_percent():
    try:
        out = subprocess.check_output(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], text=True)
        # format: "Volume: 0.85"
        return round(float(out.split(":")[1].strip().split(" ")[0]) * 100)
    except Exception:
        return 50


def set_volume_percent(percent):
    percent = max(0, min(100, percent))
    try:
        subprocess.Popen(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{percent / 100:.2f}"])
    except Exception:
        pass


def carplay_device_connected():
    try:
        out = subprocess.check_output(["lsusb"], text=True)
        return CARLINKIT_VENDOR_ID in out.lower().replace("0x", "")
    except Exception:
        return False


def read_temperature_c():
    try:
        out = subprocess.check_output(["vcgencmd", "measure_temp"], text=True)
        return float(out.split("=")[1].split("'")[0])
    except Exception:
        return None


def read_outside_temperature_c():
    """Read a future CAN/weather bridge without coupling the UI to hardware.

    A CAN reader can atomically write one number to this runtime file. Until
    that service exists, the header deliberately shows ``--°C`` rather than
    pretending that the Pi CPU temperature is the outside temperature.
    """
    candidates = (
        "/run/audi-mmi/outside-temperature",
        "/tmp/audi-mmi-outside-temperature",
    )
    for path in candidates:
        try:
            value = float(Path(path).read_text(encoding="utf-8").strip())
            if -50 <= value <= 60:
                return value
        except (OSError, ValueError):
            pass
    return None


def _set_rgba(cr, rgb, alpha=1.0):
    cr.set_source_rgba(rgb[0], rgb[1], rgb[2], alpha)


def _rounded_rect(cr, x, y, w, h, radius):
    radius = min(radius, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - radius, y + radius, radius, -math.pi / 2, 0)
    cr.arc(x + w - radius, y + h - radius, radius, 0, math.pi / 2)
    cr.arc(x + radius, y + h - radius, radius, math.pi / 2, math.pi)
    cr.arc(x + radius, y + radius, radius, math.pi, 3 * math.pi / 2)
    cr.close_path()


def _text(cr, text, x, y, size, color=(1, 1, 1), bold=False, align="left"):
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(size)
    ext = cr.text_extents(text)
    x_bearing = getattr(ext, "x_bearing", ext[0])
    width = getattr(ext, "width", ext[2])
    tx = x
    if align == "center":
        tx -= width / 2 + x_bearing
    elif align == "right":
        tx -= width + x_bearing
    _set_rgba(cr, color)
    cr.move_to(tx, y)
    cr.show_text(text)


def _paint_icon(cr, name, cx, cy, s, color=(0.97, 0.97, 0.98)):
    _set_rgba(cr, color)
    cr.set_line_width(max(3, s * 0.055))
    cr.set_line_cap(cairo.LINE_CAP_ROUND)
    cr.set_line_join(cairo.LINE_JOIN_ROUND)

    if name == "vehicle":
        # Long, low side silhouette: closer to the user's A4 Avant than the
        # generic front-view icon used in the first concept.
        cr.move_to(cx-s*.52, cy+s*.13)
        cr.curve_to(cx-s*.44, cy-s*.02, cx-s*.35, cy-s*.12, cx-s*.20, cy-s*.16)
        cr.line_to(cx-s*.05, cy-s*.34)
        cr.line_to(cx+s*.25, cy-s*.31)
        cr.line_to(cx+s*.40, cy-s*.12)
        cr.curve_to(cx+s*.49, cy-s*.08, cx+s*.53, cy, cx+s*.53, cy+s*.13)
        cr.stroke()
        cr.move_to(cx-s*.54, cy+s*.13); cr.line_to(cx+s*.55, cy+s*.13); cr.stroke()
        cr.move_to(cx-s*.02, cy-s*.32); cr.line_to(cx+s*.02, cy-s*.12)
        cr.line_to(cx+s*.32, cy-s*.12); cr.stroke()
        for wx in (-.31, .31):
            cr.arc(cx+s*wx, cy+s*.14, s*.105, 0, math.tau); cr.stroke()
    elif name == "media":
        cr.arc(cx-s*.28, cy+s*.26, s*.12, 0, math.tau); cr.stroke()
        cr.arc(cx+s*.25, cy+s*.14, s*.12, 0, math.tau); cr.stroke()
        cr.move_to(cx-s*.16, cy+s*.26); cr.line_to(cx-s*.16, cy-s*.34)
        cr.line_to(cx+s*.37, cy-s*.46); cr.line_to(cx+s*.37, cy+s*.14); cr.stroke()
    elif name == "carplay":
        for r in (.2, .34, .48):
            cr.arc(cx, cy+s*.25, s*r, math.pi*1.18, math.pi*1.82); cr.stroke()
        cr.arc(cx, cy+s*.25, s*.045, 0, math.tau); cr.fill()
    elif name == "navigation":
        cr.move_to(cx, cy-s*.45); cr.line_to(cx+s*.32, cy+s*.38)
        cr.line_to(cx, cy+s*.20); cr.line_to(cx-s*.32, cy+s*.38)
        cr.close_path(); cr.stroke()
    elif name == "radio":
        _rounded_rect(cr, cx-s*.42, cy-s*.25, s*.84, s*.56, s*.08); cr.stroke()
        cr.arc(cx-s*.22, cy+s*.04, s*.10, 0, math.tau); cr.stroke()
        cr.move_to(cx+s*.04, cy-s*.08); cr.line_to(cx+s*.29, cy-s*.08); cr.stroke()
        cr.move_to(cx+s*.04, cy+s*.08); cr.line_to(cx+s*.29, cy+s*.08); cr.stroke()
    elif name == "phone":
        cr.arc(cx, cy, s*.36, math.pi*.67, math.pi*1.78); cr.stroke()
    elif name == "settings":
        cr.arc(cx, cy, s*.18, 0, math.tau); cr.stroke()
        for i in range(8):
            a = i*math.pi/4
            cr.move_to(cx+math.cos(a)*s*.27, cy+math.sin(a)*s*.27)
            cr.line_to(cx+math.cos(a)*s*.42, cy+math.sin(a)*s*.42); cr.stroke()
    else:
        cr.arc(cx, cy, s*.34, 0, math.tau); cr.stroke()


class SettingsStore:
    """Small, durable settings file used by the launcher and future services."""

    DEFAULTS = {
        "volume": 50,
        "brightness": 80,
        "display_mode": "Auto",
        "screen_timeout": "Nie",
        "startup": "Hauptmenü",
        "animations": True,
        "touch_sounds": False,
        "background_strength": 68,
    }

    def __init__(self):
        self.path = Path.home() / ".config" / "audi-mmi" / "settings.json"
        self.data = dict(self.DEFAULTS)
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.data.update({k: v for k, v in loaded.items() if k in self.DEFAULTS})
        except (OSError, ValueError, TypeError):
            pass
        self.data["volume"] = read_volume_percent()

    def set(self, key, value):
        if key not in self.DEFAULTS:
            return
        self.data[key] = value
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
            temporary.replace(self.path)
        except OSError:
            pass


class SettingsView(Gtk.DrawingArea):
    """Touch-first settings page without desktop-style GTK dialogs."""

    def __init__(self, owner, store):
        super().__init__()
        self.owner, self.store = owner, store
        self.hitboxes = []
        bg_path = Path(__file__).resolve().parent / "assets" / "alps-background.png"
        try:
            self.background = cairo.ImageSurface.create_from_png(str(bg_path))
        except (OSError, cairo.Error):
            self.background = None
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.TOUCH_MASK)
        self.connect("draw", self._draw)
        self.connect("button-release-event", self._release)
        self.connect("touch-event", self._touch)

    def _button(self, cr, ident, box, label, value, accent=(.86, .08, .16)):
        x, y, w, h = box
        _rounded_rect(cr, x, y, w, h, 17)
        _set_rgba(cr, (.055, .058, .07), .91); cr.fill_preserve()
        _set_rgba(cr, (.34, .35, .39), .9); cr.set_line_width(1.5); cr.stroke()
        _text(cr, label, x+24, y+32, 15, (.68, .69, .73), True)
        value_text = str(value)
        value_size = 18 if len(value_text) > 27 else 20 if len(value_text) > 20 else 23
        _text(cr, value_text, x+24, y+69, value_size, (1,1,1), True)
        _set_rgba(cr, accent); cr.arc(x+w-29, y+h/2, 6, 0, math.tau); cr.fill()
        self.hitboxes.append((ident, x, y, w, h))

    def _draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        cr.save(); cr.scale(w/1600.0, h/720.0)
        if self.background:
            cr.set_source_surface(self.background, 0, 0); cr.paint()
        else:
            cr.set_source_rgb(.02,.02,.03); cr.paint()
        # Keep the same Alpine identity on every page while preserving enough
        # contrast for controls and small status text.
        cr.set_source_rgba(.01,.01,.02,.48); cr.rectangle(0,0,1600,720); cr.fill()
        self.hitboxes = []
        _rounded_rect(cr, 34, 22, 116, 46, 23); _set_rgba(cr, (.10,.10,.12), .94); cr.fill()
        _text(cr, "‹  ZURÜCK", 92, 52, 14, (1,1,1), True, "center")
        self.hitboxes.append(("back", 34, 22, 116, 46))
        _text(cr, "Einstellungen", 190, 56, 31, (1,1,1), True)
        _text(cr, "Display · Audio · CarPlay · Fahrzeug", 190, 81, 15, (.7,.7,.74))

        d = self.store.data
        cards = [
            ("volume_down", "Audio", f"Lautstärke  {d['volume']} %", (.65,.08,.16)),
            ("brightness", "Display", f"Helligkeit  {d['brightness']} %", (.10,.36,.68)),
            ("display_mode", "Darstellung", d["display_mode"], (.43,.20,.70)),
            ("screen_timeout", "Bildschirm aus", d["screen_timeout"], (.17,.45,.52)),
            ("startup", "Startansicht", d["startup"], (.10,.48,.30)),
            ("animations", "Animationen", "Ein" if d["animations"] else "Aus", (.70,.34,.08)),
            ("touch_sounds", "Tastentöne", "Ein" if d["touch_sounds"] else "Aus", (.45,.25,.18)),
            ("background_strength", "Alpen-Hintergrund", f"{d['background_strength']} %", (.36,.38,.42)),
            ("network", "Verbindungen", "WLAN · Bluetooth", (.08,.37,.62)),
            ("carplay", "Apple CarPlay", "Dongle- und Audiostatus", (.08,.48,.27)),
            ("vehicle", "Fahrzeug & CAN", "Hardware noch nicht verbunden", (.68,.06,.12)),
            ("system", "System", "Temperatur · Speicher · Updates", (.28,.30,.34)),
        ]
        for i, (ident, label, value, accent) in enumerate(cards):
            col, row = i % 4, i // 4
            self._button(cr, ident, (42+col*389, 116+row*174, 363, 143), label, value, accent)
        _text(cr, "Lautstärke: tippen = +5 %, lange Regelung folgt über die Lenkrad-/CAN-Anbindung.", 44, 683, 14, (.62,.62,.66))
        cr.restore(); return False

    def _activate(self, ident):
        d = self.store.data
        if ident == "back":
            self.owner.on_go_home(); return
        if ident == "volume_down":
            value = (int(d["volume"]) + 5) % 105
            self.store.set("volume", value); set_volume_percent(value)
        elif ident == "brightness":
            self.store.set("brightness", 25 if int(d["brightness"]) >= 100 else int(d["brightness"]) + 25)
        elif ident == "display_mode":
            options = ["Auto", "Tag", "Nacht"]
            self.store.set("display_mode", options[(options.index(d["display_mode"]) + 1) % len(options)])
        elif ident == "screen_timeout":
            options = ["Nie", "30 Sek.", "2 Min.", "5 Min."]
            self.store.set("screen_timeout", options[(options.index(d["screen_timeout"]) + 1) % len(options)])
        elif ident == "startup":
            self.store.set("startup", "CarPlay" if d["startup"] == "Hauptmenü" else "Hauptmenü")
        elif ident in ("animations", "touch_sounds"):
            self.store.set(ident, not bool(d[ident]))
        elif ident == "background_strength":
            self.store.set(ident, 35 if int(d[ident]) >= 85 else int(d[ident]) + 10)
        elif ident in ("network", "carplay", "vehicle", "system"):
            self.owner.show_info({"network":"Verbindungen", "carplay":"Apple CarPlay", "vehicle":"Fahrzeug & CAN", "system":"System"}[ident],
                                 "Die Detailseite ist vorbereitet. Fahrzeugwerte werden freigeschaltet, sobald der CAN-Adapter angeschlossen und geprüft ist.")
        self.queue_draw()

    def _release(self, _widget, event):
        sx, sy = 1600/self.get_allocated_width(), 720/self.get_allocated_height()
        x, y = event.x*sx, event.y*sy
        for ident, bx, by, bw, bh in self.hitboxes:
            if bx <= x <= bx+bw and by <= y <= by+bh:
                self._activate(ident); break
        return True

    def _touch(self, _widget, event):
        if event.type == Gdk.EventType.TOUCH_END:
            return self._release(_widget, event)
        return True


class NavigationView(Gtk.DrawingArea):
    """MMI navigation hub with Kies Drive as the primary destination."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.hitboxes = []
        bg_path = Path(__file__).resolve().parent / "assets" / "alps-background.png"
        try:
            self.background = cairo.ImageSurface.create_from_png(str(bg_path))
        except (OSError, cairo.Error):
            self.background = None
        self.add_events(Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.TOUCH_MASK)
        self.connect("draw", self._draw)
        self.connect("button-release-event", self._release)
        self.connect("touch-event", self._touch)

    def _card(self, cr, ident, box, title, subtitle, color, primary=False):
        x, y, w, h = box
        _rounded_rect(cr, x, y, w, h, 28)
        _set_rgba(cr, color, .94 if primary else .88)
        cr.fill_preserve()
        _set_rgba(cr, tuple(min(1, value * 1.9) for value in color), .95)
        cr.set_line_width(2)
        cr.stroke()

        icon_size = 118 if primary else 94
        _paint_icon(cr, "navigation" if ident == "kies_drive" else "carplay",
                    x + 108, y + h / 2, icon_size)
        _text(cr, title, x + 205, y + 82, 35 if primary else 30, (1, 1, 1), True)
        _text(cr, subtitle, x + 205, y + 122, 17, (.82, .84, .89))

        button_w = 184 if primary else 160
        _rounded_rect(cr, x + w - button_w - 34, y + h / 2 - 25, button_w, 50, 25)
        _set_rgba(cr, (1, 1, 1), .97)
        cr.fill()
        _text(cr, "KIES DRIVE" if primary else "CARPLAY",
              x + w - button_w / 2 - 34, y + h / 2 + 6, 15,
              (.06, .08, .13) if primary else (.03, .20, .12), True, "center")
        self.hitboxes.append((ident, x, y, w, h))

    def _draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        cr.save()
        cr.scale(w / 1600.0, h / 720.0)
        if self.background:
            cr.set_source_surface(self.background, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(.02, .02, .03)
            cr.paint()
        cr.set_source_rgba(.01, .01, .02, .48)
        cr.rectangle(0, 0, 1600, 720)
        cr.fill()

        self.hitboxes = []
        _rounded_rect(cr, 34, 22, 116, 46, 23)
        _set_rgba(cr, (.10, .10, .12), .94)
        cr.fill()
        _text(cr, "‹  ZURÜCK", 92, 52, 14, (1, 1, 1), True, "center")
        self.hitboxes.append(("back", 34, 22, 116, 46))
        _text(cr, "Navigation", 190, 56, 31, (1, 1, 1), True)
        _text(cr, "Karte · Routen · Ziele", 190, 81, 15, (.7, .7, .74))

        self._card(
            cr, "kies_drive", (82, 128, 1436, 224), "Kies Drive",
            "Deine eigene Navigation mit Routen, Tankstellen und Reiseplanung",
            (.035, .16, .34), True,
        )
        self._card(
            cr, "carplay", (82, 390, 1436, 176), "Navigation über CarPlay",
            "Apple Karten und weitere Apps vom iPhone",
            (.025, .25, .16), False,
        )
        _text(cr, "Kies Drive ist die Standardauswahl in diesem Menü.",
              84, 626, 15, (.70, .71, .75))
        cr.restore()
        return False

    def _activate(self, ident):
        if ident == "back":
            self.owner.on_go_home()
        elif ident == "kies_drive":
            self.owner.on_start_kies_drive()
        elif ident == "carplay":
            self.owner.on_start_carplay()

    def _release(self, _widget, event):
        sx, sy = 1600 / self.get_allocated_width(), 720 / self.get_allocated_height()
        x, y = event.x * sx, event.y * sy
        for ident, bx, by, bw, bh in self.hitboxes:
            if bx <= x <= bx + bw and by <= y <= by + bh:
                self._activate(ident)
                break
        return True

    def _touch(self, _widget, event):
        if event.type == Gdk.EventType.TOUCH_END:
            return self._release(_widget, event)
        return True


class CarouselView(Gtk.DrawingArea):
    """Single lightweight canvas: swipeable, animated-looking MMI carousel."""

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.selected = 0
        self.press_x = None
        self.connected = False
        self.outside_temp = None
        self.items = [
            ("vehicle", "Fahrzeug", "Verbrauch · Fahrzeugstatus · Service", (0.43, .04, .10), owner.on_open_vehicle),
            ("carplay", "Apple CarPlay", "Bereit zum Verbinden", (.03, .26, .17), owner.on_start_carplay),
            ("navigation", "Navigation", "Kies Drive · CarPlay", (.04, .14, .30), owner.on_open_navigation),
            ("media", "Media", "USB · Bluetooth · CarPlay", (.23, .08, .29), lambda *_: owner.show_info("Media", "Medien werden über CarPlay oder den Audi-Audioeingang wiedergegeben.")),
            ("radio", "Radio", "FM · Sender · Favoriten", (.28, .09, .12), lambda *_: owner.show_info("Radio", "FM bleibt im originalen Audi-Radio. Die Senderanzeige und Bedienung werden nach der CAN/MMI-Anbindung in diese Oberfläche übernommen.")),
            ("phone", "Telefon", "Anrufe und Kontakte", (.05, .23, .27), lambda *_: owner.show_info("Telefon", "Telefonie wird über CarPlay bereitgestellt.")),
            ("settings", "Einstellungen", "Display · Audio · System", (.23, .23, .25), owner.on_open_settings),
            ("system", "System", "Status · Updates · Diagnose", (.15, .18, .23), owner.on_open_settings),
        ]
        bg_path = Path(__file__).resolve().parent / "assets" / "alps-background.png"
        try:
            self.background = cairo.ImageSurface.create_from_png(str(bg_path))
        except (OSError, cairo.Error):
            self.background = None
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.TOUCH_MASK
        )
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._press)
        self.connect("button-release-event", self._release)
        self.connect("touch-event", self._touch)

    def _press(self, _widget, event):
        self.press_x = event.x
        return True

    def _release(self, _widget, event):
        if self.press_x is None:
            return True
        dx = event.x - self.press_x
        self.press_x = None
        if abs(dx) > 75:
            self.selected = (self.selected - 1 if dx > 0 else self.selected + 1) % len(self.items)
        elif event.x < self.get_allocated_width() * .30:
            self.selected = (self.selected - 1) % len(self.items)
        elif event.x > self.get_allocated_width() * .70:
            self.selected = (self.selected + 1) % len(self.items)
        else:
            self.items[self.selected][4]()
        self.queue_draw()
        return True

    def _touch(self, _widget, event):
        if event.type == Gdk.EventType.TOUCH_BEGIN:
            self.press_x = event.x
        elif event.type == Gdk.EventType.TOUCH_END:
            return self._release(_widget, event)
        return True

    def _card(self, cr, item, x, y, w, h, selected=False):
        icon, title, subtitle, rgb, _action = item
        _rounded_rect(cr, x, y, w, h, 28 if selected else 23)
        _set_rgba(cr, rgb, .93 if selected else .88); cr.fill_preserve()
        _set_rgba(cr, (0.9, .18, .28) if selected else tuple(min(1, c*1.8) for c in rgb), .95)
        cr.set_line_width(2); cr.stroke()
        _text(cr, title.upper(), x+36, y+48, 16, (.88, .72, .75) if selected else (.72, .72, .76), True)
        _paint_icon(cr, icon, x+w/2, y+h*.46, 132 if selected else 84)
        _text(cr, title, x+w/2, y+h-104, 34 if selected else 24, (1,1,1), True, "center")
        _text(cr, subtitle, x+w/2, y+h-68, 17 if selected else 15, (.82,.75,.77), False, "center")
        if selected:
            _rounded_rect(cr, x+w/2-80, y+h-49, 160, 40, 20)
            _set_rgba(cr, (1,1,1)); cr.fill()
            _text(cr, "ÖFFNEN", x+w/2, y+h-23, 14, (.23,.03,.06), True, "center")

    def _draw(self, _widget, cr):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        sx, sy = w / 1600.0, h / 720.0
        cr.save(); cr.scale(sx, sy)
        if self.background:
            cr.set_source_surface(self.background, 0, 0); cr.paint()
        else:
            cr.set_source_rgb(.02, .02, .03); cr.paint()
        cr.set_source_rgba(.01, .01, .02, .34); cr.rectangle(0,0,1600,720); cr.fill()

        _text(cr, "AUDI MMI", 42, 47, 18, (.91,.91,.93), True)
        _text(cr, "Hauptmenü", 800, 50, 25, (1,1,1), True, "center")
        _text(cr, time.strftime("%H:%M"), 1518, 49, 24, (1,1,1), True, "right")
        temp = "--°C" if self.outside_temp is None else f"{round(self.outside_temp)}°C"
        _text(cr, temp, 1432, 47, 17, (.91,.91,.93), True, "right")
        _text(cr, "CarPlay" if self.connected else "CarPlay bereit", 1302, 45, 15, (.72,.72,.75), False, "right")
        _set_rgba(cr, (.34,.82,.44) if self.connected else (.42,.42,.45)); cr.arc(1327, 40, 5, 0, math.tau); cr.fill()
        cr.set_source_rgba(.4,.4,.43,.5); cr.set_line_width(1); cr.move_to(32,72); cr.line_to(1568,72); cr.stroke()

        n = len(self.items)
        previous = self.items[(self.selected-1) % n]
        current = self.items[self.selected]
        following = self.items[(self.selected+1) % n]
        self._card(cr, previous, 170, 152, 350, 448, False)
        self._card(cr, following, 1080, 152, 350, 448, False)
        self._card(cr, current, 472, 112, 656, 513, True)
        _text(cr, f"{self.selected+1} / {n}", 1080, 167, 15, (.86,.56,.60), False, "right")

        start = 800 - ((n-1)*17+28)/2
        for i in range(n):
            x = start + i*17
            if i == self.selected:
                _rounded_rect(cr, x, 654, 28, 6, 3); _set_rgba(cr, (.89,.1,.18)); cr.fill()
            else:
                _set_rgba(cr, (.46,.46,.49)); cr.arc(x+13, 657, 3, 0, math.tau); cr.fill()
        _text(cr, "‹", 43, 692, 36, (.76,.76,.78))
        _text(cr, "›", 1557, 692, 36, (.76,.76,.78), False, "right")
        _text(cr, "Wischen oder antippen", 800, 703, 13, (.52,.52,.55), False, "center")
        cr.restore()
        return False


class Launcher(Gtk.Window):
    def __init__(self):
        super().__init__(title="MMI")
        self.fullscreen()
        self.set_decorated(False)

        self.settings_store = SettingsStore()
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(220)
        self.carousel = CarouselView(self)
        self.settings_view = SettingsView(self, self.settings_store)
        self.navigation_view = NavigationView(self)
        self.stack.add_named(self.carousel, "home")
        self.stack.add_named(self.settings_view, "settings")
        self.stack.add_named(self.navigation_view, "navigation")
        self.add(self.stack)

        GLib.timeout_add_seconds(1, self._tick_clock)
        GLib.timeout_add_seconds(4, self._tick_status)
        self._tick_clock()
        self._tick_status()

    def _build_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        rail.get_style_context().add_class("rail")
        rail.set_size_request(104, -1)
        rail.set_margin_top(16)
        rail.set_margin_bottom(16)

        GREY = (0.85, 0.85, 0.86)
        DANGER = (0.886, 0.0, 0.102)

        def rail_button(icon_name, action, danger=False):
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.add(draw_icon(icon_name, DANGER if danger else GREY))
            btn.get_style_context().add_class("rail-btn")
            if danger:
                btn.get_style_context().add_class("rail-btn-danger")
            btn.connect("clicked", action)
            rail.pack_start(btn, False, False, 0)
            return btn

        home = rail_button("home", self.on_go_home)
        home.get_style_context().add_class("rail-btn-active")
        rail_button("carplay", self.on_start_carplay)
        rail_button("vehicle", self.on_open_vehicle)
        rail_button("settings", self.on_open_settings)

        spacer = Gtk.Box()
        rail.pack_start(spacer, True, True, 0)

        rail_button("shutdown", self.on_shutdown, danger=True)
        return rail

    def _build_statusbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bar.get_style_context().add_class("statusbar")
        bar.set_size_request(-1, 108)
        bar.set_margin_start(24)
        bar.set_margin_end(30)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_valign(Gtk.Align.CENTER)
        title = Gtk.Label(label="Startseite")
        title.set_halign(Gtk.Align.START)
        title.get_style_context().add_class("page-title")
        subtitle = Gtk.Label(label="Audi MMI")
        subtitle.set_halign(Gtk.Align.START)
        subtitle.get_style_context().add_class("page-subtitle")
        title_box.pack_start(title, False, False, 0)
        title_box.pack_start(subtitle, False, False, 0)
        left = title_box
        bar.pack_start(left, True, True, 0)

        self.conn_label = Gtk.Label(label="CarPlay")
        self.conn_label.get_style_context().add_class("status-label")
        self.dot = Gtk.Box()
        self.dot.get_style_context().add_class("dot")
        self.clock_label = Gtk.Label(label="--:--")
        self.clock_label.get_style_context().add_class("clock")
        right = Gtk.Box(spacing=14)
        right.set_valign(Gtk.Align.CENTER)
        right.pack_start(self.conn_label, False, False, 0)
        right.pack_start(self.dot, False, False, 0)
        right.pack_start(self.clock_label, False, False, 0)
        bar.pack_end(right, False, False, 0)
        return bar

    def _build_grid(self):
        grid = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
        grid.set_column_spacing(12)
        grid.set_row_spacing(12)
        grid.set_margin_start(24)
        grid.set_margin_end(30)
        grid.set_margin_top(20)
        grid.set_margin_bottom(26)

        # Echtes Audi-MMI-Vorbild: Icons sind schlicht hellgrau/weiss, die
        # Kategorie-Farbe steckt nur im duennen Strich unter dem Icon - nicht
        # im Icon selbst wie in der ersten Fassung.
        ICON_COLOR = (0.92, 0.92, 0.93)
        ACCENTS = {
            "carplay": "#3fae3f",
            "vehicle": "#e2001a",
            "settings": "#b0b0b0",
        }

        def tile(icon_name, label_text, action):
            # Jede Kachel bleibt antippbar - auch die, hinter denen noch
            # keine echte Funktion steckt. Ein totes, nicht reagierendes
            # Icon fuehlt sich auf einem Touchscreen wie ein defektes
            # Geraet an, auch wenn es "nur" ein Hinweistext ist.
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("tile")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.set_margin_start(20)
            box.set_margin_end(20)
            box.set_margin_top(18)
            box.set_margin_bottom(14)
            icon_wrap = Gtk.Box()
            icon_wrap.set_halign(Gtk.Align.CENTER)
            icon_wrap.set_valign(Gtk.Align.CENTER)
            icon = draw_icon(icon_name, ICON_COLOR)
            icon.set_size_request(72, 72)
            icon_wrap.pack_start(icon, False, False, 0)
            underline = Gtk.Box()
            underline.set_size_request(62, 4)
            line_color = ACCENTS.get(icon_name, "#657d99")
            css = Gtk.CssProvider()
            css.load_from_data(
                f"box {{ background-color: {line_color}; border-radius: 2px; }}".encode()
            )
            underline.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.get_style_context().add_class("tile-label")
            box.pack_start(icon_wrap, True, True, 0)
            box.pack_start(label, False, False, 0)
            box.pack_start(underline, False, False, 0)
            btn.add(box)
            btn.connect("clicked", action)
            return btn

        def covered_by_carplay(name):
            return lambda *_a: self.show_info(
                name, "Wird von CarPlay über dein iPhone bereitgestellt, sobald der Dongle verbunden ist."
            )

        # Layout an das echte Audi-MMI-Raster angelehnt (4x2). Radio/Media/
        # Telefon/Nachrichten/Navigation gibt es bei uns nicht als eigene
        # Funktion, weil CarPlay das vom iPhone aus übernimmt - antippbar
        # bleiben sie trotzdem, mit einem ehrlichen Hinweis statt totem Icon.
        grid.attach(tile("radio", "Radio", covered_by_carplay("Radio")), 0, 0, 1, 1)
        grid.attach(tile("media", "Media", covered_by_carplay("Media")), 1, 0, 1, 1)
        grid.attach(tile("phone", "Telefon", covered_by_carplay("Telefon")), 2, 0, 1, 1)
        grid.attach(tile("navigation", "Navigation", self.on_open_navigation), 3, 0, 1, 1)
        grid.attach(tile("carplay", "Apple CarPlay", self.on_start_carplay), 0, 1, 1, 1)
        grid.attach(tile("vehicle", "Fahrzeug", self.on_open_vehicle), 1, 1, 1, 1)
        grid.attach(tile("settings", "Einstellungen", self.on_open_settings), 2, 1, 1, 1)
        grid.attach(tile("home", "System", self.on_open_settings), 3, 1, 1, 1)
        return grid

    def _tick_clock(self):
        self.carousel.queue_draw()
        return True

    def _tick_status(self):
        online = carplay_device_connected()
        self.carousel.connected = online
        self.carousel.outside_temp = read_outside_temperature_c()
        self.carousel.queue_draw()
        return True

    def on_start_carplay(self, *_args):
        # Signals kiosk-runner.sh to relaunch cage with the CarPlay AppImage
        # once this GTK process (and its cage instance) exits - cage only
        # ever hosts one client for its lifetime, so switching apps means
        # handing off between two separate cage runs, not hiding a window.
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        marker_dir = os.path.join(runtime_dir, "audi-mmi")
        os.makedirs(marker_dir, exist_ok=True)
        with open(os.path.join(marker_dir, "next-app"), "w") as f:
            f.write("carplay")
        Gtk.main_quit()

    def on_go_home(self, *_args):
        self.stack.set_visible_child_name("home")

    def on_open_navigation(self, *_args):
        self.navigation_view.queue_draw()
        self.stack.set_visible_child_name("navigation")

    def on_start_kies_drive(self, *_args):
        if not os.path.isfile(KIES_DRIVE_EXECUTABLE) or not os.access(KIES_DRIVE_EXECUTABLE, os.X_OK):
            self.show_info(
                "Kies Drive",
                "Kies Drive ist im Navigationsmenü eingerichtet. Für den Start auf dem "
                "Raspberry Pi fehlt noch die Linux/ARM64-Ausgabe der App.",
            )
            return
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        marker_dir = os.path.join(runtime_dir, "audi-mmi")
        os.makedirs(marker_dir, exist_ok=True)
        with open(os.path.join(marker_dir, "next-app"), "w") as f:
            f.write("kies-drive")
        Gtk.main_quit()

    def show_info(self, title, message):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_open_vehicle(self, *_args):
        self.show_info(
            "Fahrzeugdaten",
            "Noch nicht verfügbar - wartet auf CAN-Bus-Hardware "
            "(Bordspannung, Kühlmitteltemperatur, Verbrauch etc. folgen, "
            "sobald die Auslesehardware angeschlossen ist).",
        )

    def on_open_settings(self, *_args):
        self.settings_view.queue_draw()
        self.stack.set_visible_child_name("settings")

    def on_shutdown(self, *_args):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Wirklich herunterfahren?",
        )
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.YES:
            subprocess.Popen(["sudo", "systemctl", "poweroff"])


def main():
    style_provider = Gtk.CssProvider()
    style_provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        style_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    win = Launcher()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
