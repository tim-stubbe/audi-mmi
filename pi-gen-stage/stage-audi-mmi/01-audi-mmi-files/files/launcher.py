#!/usr/bin/env python3
"""Native GTK kiosk launcher for the Audi MMI project.

Replaces the earlier Chromium-based launcher: runs as the single client
under the 'cage' Wayland kiosk compositor, using GTK3 directly instead of
a browser engine. On the Pi Zero 2 W (512MB RAM) this uses roughly
15-20MB instead of Chromium's 150-200MB, leaving far more headroom for
react-carplay when it is actually running.
"""

import os
import subprocess
import time

import math

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
CARLINKIT_VENDOR_ID = "1314"

CSS = b"""
window { background-color: #050505; }
.rail { background-color: #0c0c0d; border-right: 1px solid #232325; }
.rail-btn { min-width: 52px; min-height: 52px; border-radius: 12px;
            background: transparent; color: #7c7c80; border: none; }
.rail-btn:hover { background-color: #1c1c1e; color: #f2f2f3; }
.rail-btn-danger { color: #7a1620; }
.statusbar { border-bottom: 1px solid #232325; }
.status-label { color: #7c7c80; font-size: 14px; }
.chip { border: 1px solid #232325; border-radius: 999px; padding: 3px 12px;
        color: #7c7c80; font-size: 14px; }
.clock { color: #f2f2f3; font-size: 18px; }
.tile { background: transparent; border: none; border-radius: 0;
        border-right: 1px solid #232325; border-bottom: 1px solid #232325; }
.tile:hover { background-color: #101011; }
.tile-label { color: #f2f2f3; font-size: 16px; font-weight: bold; letter-spacing: 0.5px; }
.tile-label-disabled { color: #4a4a4d; font-size: 16px; font-weight: bold; letter-spacing: 0.5px; }
.dot { min-width: 8px; min-height: 8px; border-radius: 4px; background-color: #7c7c80; }
.dot-online { background-color: #3ecf5f; }
"""


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


class Launcher(Gtk.Window):
    def __init__(self):
        super().__init__(title="MMI")
        self.fullscreen()
        self.set_decorated(False)

        root = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add(root)

        root.pack_start(self._build_rail(), False, False, 0)

        main = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root.pack_start(main, True, True, 0)
        main.pack_start(self._build_statusbar(), False, False, 0)
        main.pack_start(self._build_grid(), True, True, 0)

        GLib.timeout_add_seconds(1, self._tick_clock)
        GLib.timeout_add_seconds(4, self._tick_status)
        self._tick_clock()
        self._tick_status()

    def _build_rail(self):
        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        rail.get_style_context().add_class("rail")
        rail.set_size_request(84, -1)
        rail.set_margin_top(22)
        rail.set_margin_bottom(22)

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

        rail_button("home", self.on_go_home)
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
        bar.set_size_request(-1, 52)
        bar.set_margin_start(32)
        bar.set_margin_end(32)

        self.dot = Gtk.Box()
        self.dot.get_style_context().add_class("dot")
        self.conn_label = Gtk.Label(label="Kein Gerät verbunden")
        self.conn_label.get_style_context().add_class("status-label")
        left = Gtk.Box(spacing=10)
        left.pack_start(self.dot, False, False, 0)
        left.pack_start(self.conn_label, False, False, 0)
        bar.pack_start(left, True, True, 0)

        self.temp_chip = Gtk.Label(label="--°C")
        self.temp_chip.get_style_context().add_class("chip")
        self.clock_label = Gtk.Label(label="--:--")
        self.clock_label.get_style_context().add_class("clock")
        right = Gtk.Box(spacing=20)
        right.pack_start(self.temp_chip, False, False, 0)
        right.pack_start(self.clock_label, False, False, 0)
        bar.pack_end(right, False, False, 0)
        return bar

    def _build_grid(self):
        grid = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)

        # Echtes Audi-MMI-Vorbild: Icons sind schlicht hellgrau/weiss, die
        # Kategorie-Farbe steckt nur im duennen Strich unter dem Icon - nicht
        # im Icon selbst wie in der ersten Fassung.
        ICON_COLOR = (0.92, 0.92, 0.93)
        ACCENTS = {
            "carplay": "#3fae3f",
            "vehicle": "#e2001a",
            "settings": "#b0b0b0",
        }

        DISABLED_ICON = (0.42, 0.42, 0.44)
        DISABLED_LINE = "#3a3a3d"

        def tile(icon_name, label_text, action=None, disabled=False):
            btn = Gtk.Button()
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("tile")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            box.set_halign(Gtk.Align.CENTER)
            box.set_valign(Gtk.Align.CENTER)
            icon = draw_icon(icon_name, DISABLED_ICON if disabled else ICON_COLOR)
            icon.set_size_request(64, 64)
            underline = Gtk.Box()
            underline.set_size_request(44, 4)
            line_color = DISABLED_LINE if disabled else ACCENTS[icon_name]
            css = Gtk.CssProvider()
            css.load_from_data(
                f"box {{ background-color: {line_color}; border-radius: 2px; }}".encode()
            )
            underline.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            label = Gtk.Label(label=label_text.upper())
            label.get_style_context().add_class("tile-label-disabled" if disabled else "tile-label")
            box.pack_start(icon, False, False, 0)
            box.pack_start(underline, False, False, 0)
            box.pack_start(label, False, False, 0)
            btn.add(box)
            if disabled:
                btn.set_sensitive(False)
            else:
                btn.connect("clicked", action)
            return btn

        # Layout an das echte Audi-MMI-Raster angelehnt (4x2). Radio/Media/
        # Telefon/Nachrichten/Navigation sind bei uns deaktiviert, weil
        # CarPlay diese Funktionen bereits vom iPhone aus übernimmt - hier
        # nur fuers Layout, keine erfundene Funktionalitaet dahinter.
        grid.attach(tile("radio", "Radio", disabled=True), 0, 0, 1, 1)
        grid.attach(tile("media", "Media", disabled=True), 1, 0, 1, 1)
        grid.attach(tile("phone", "Telefon", disabled=True), 2, 0, 1, 1)
        grid.attach(tile("messages", "Nachrichten", disabled=True), 3, 0, 1, 1)
        grid.attach(tile("navigation", "Navigation", disabled=True), 0, 1, 1, 1)
        grid.attach(tile("vehicle", "Fahrzeug", self.on_open_vehicle), 1, 1, 1, 1)
        grid.attach(tile("settings", "Einstell.", self.on_open_settings), 2, 1, 1, 1)
        grid.attach(tile("carplay", "CarPlay", self.on_start_carplay), 3, 1, 1, 1)
        return grid

    def _tick_clock(self):
        self.clock_label.set_text(time.strftime("%H:%M"))
        return True

    def _tick_status(self):
        temp = read_temperature_c()
        if temp is not None:
            self.temp_chip.set_text(f"{round(temp)}°C")
        online = carplay_device_connected()
        ctx = self.dot.get_style_context()
        if online:
            ctx.add_class("dot-online")
            self.conn_label.set_text("Gerät verbunden")
        else:
            ctx.remove_class("dot-online")
            self.conn_label.set_text("Kein Gerät verbunden")
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
        pass  # already home; kept as a harmless no-op for the rail button

    def on_open_vehicle(self, *_args):
        pass  # Fahrzeugdaten-Seite folgt, sobald CAN-Hardware vorhanden ist

    def on_open_settings(self, *_args):
        pass  # Platzhalter fuer spaetere Einstellungen

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
