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
        grid.attach(tile("navigation", "Navigation", covered_by_carplay("Navigation")), 3, 0, 1, 1)
        grid.attach(tile("carplay", "Apple CarPlay", self.on_start_carplay), 0, 1, 1, 1)
        grid.attach(tile("vehicle", "Fahrzeug", self.on_open_vehicle), 1, 1, 1, 1)
        grid.attach(tile("settings", "Einstellungen", self.on_open_settings), 2, 1, 1, 1)
        grid.attach(tile("home", "System", self.on_open_settings), 3, 1, 1, 1)
        return grid

    def _tick_clock(self):
        self.clock_label.set_text(time.strftime("%H:%M"))
        return True

    def _tick_status(self):
        online = carplay_device_connected()
        ctx = self.dot.get_style_context()
        if online:
            ctx.add_class("dot-online")
            self.conn_label.set_text("CarPlay")
        else:
            ctx.remove_class("dot-online")
            self.conn_label.set_text("CarPlay bereit")
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
        dialog = Gtk.Dialog(title="Einstellungen", transient_for=self, flags=0)
        dialog.add_buttons("Schließen", Gtk.ResponseType.CLOSE)
        dialog.set_default_size(480, 200)
        content = dialog.get_content_area()
        content.set_spacing(16)
        content.set_border_width(24)

        vol_label = Gtk.Label(label="Lautstärke (HDMI-Audio)")
        vol_label.set_halign(Gtk.Align.START)
        content.pack_start(vol_label, False, False, 0)

        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 5)
        scale.set_value(read_volume_percent())
        scale.connect("value-changed", lambda s: set_volume_percent(int(s.get_value())))
        content.pack_start(scale, False, False, 0)

        dialog.show_all()
        dialog.run()
        dialog.destroy()

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
