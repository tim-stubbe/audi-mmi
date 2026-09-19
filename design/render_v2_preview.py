#!/usr/bin/env python3
"""Render the proposed 1600x720 Audi MMI launcher without GTK/Pi hardware."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

W, H = 1600, 720
OUT = Path(__file__).with_name("mmi-v2-preview.png")

BG = "#070708"
PANEL = "#111113"
PANEL_HOVER = "#171719"
LINE = "#29292d"
TEXT = "#f1f1f3"
MUTED = "#8b8b91"
RED = "#e21b2d"


def font(size, bold=False):
    paths = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


im = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(im)


def rr(box, radius, fill, outline=None, width=1):
    d.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def line(points, fill=TEXT, width=4):
    d.line(points, fill=fill, width=width, joint="curve")


def icon_home(cx, cy, s, color):
    line([(cx-s*.32, cy), (cx, cy-s*.28), (cx+s*.32, cy)], color, 4)
    d.rounded_rectangle((cx-s*.23, cy, cx+s*.23, cy+s*.25), 4, outline=color, width=4)


def icon_phone(cx, cy, s, color):
    d.arc((cx-s*.3, cy-s*.38, cx+s*.3, cy+s*.38), 120, 300, fill=color, width=5)
    d.ellipse((cx-s*.31, cy+s*.18, cx-s*.15, cy+s*.34), outline=color, width=4)
    d.ellipse((cx+s*.15, cy-s*.34, cx+s*.31, cy-s*.18), outline=color, width=4)


def icon_music(cx, cy, s, color):
    d.ellipse((cx-s*.36, cy+s*.12, cx-s*.08, cy+s*.4), outline=color, width=4)
    d.ellipse((cx+s*.08, cy, cx+s*.36, cy+s*.28), outline=color, width=4)
    line([(cx-s*.08, cy+s*.25), (cx-s*.08, cy-s*.34), (cx+s*.36, cy-s*.43), (cx+s*.36, cy+s*.12)], color, 4)


def icon_nav(cx, cy, s, color):
    pts = [(cx, cy-s*.42), (cx+s*.32, cy+s*.36), (cx, cy+s*.2), (cx-s*.32, cy+s*.36)]
    d.polygon(pts, outline=color)
    line(pts+[pts[0]], color, 4)


def icon_car(cx, cy, s, color):
    line([(cx-s*.38, cy+s*.12), (cx-s*.25, cy-s*.2), (cx+s*.25, cy-s*.2), (cx+s*.38, cy+s*.12)], color, 4)
    line([(cx-s*.42, cy+s*.12), (cx+s*.42, cy+s*.12)], color, 4)
    d.ellipse((cx-s*.28, cy+s*.12, cx-s*.12, cy+s*.28), outline=color, width=4)
    d.ellipse((cx+s*.12, cy+s*.12, cx+s*.28, cy+s*.28), outline=color, width=4)


def icon_gear(cx, cy, s, color):
    d.ellipse((cx-s*.18, cy-s*.18, cx+s*.18, cy+s*.18), outline=color, width=4)
    for i in range(8):
        a = i*math.pi/4
        line([(cx+math.cos(a)*s*.27, cy+math.sin(a)*s*.27),
              (cx+math.cos(a)*s*.41, cy+math.sin(a)*s*.41)], color, 5)


def icon_carplay(cx, cy, s, color):
    for r in (.18, .30, .42):
        d.arc((cx-s*r, cy-s*r*.3, cx+s*r, cy+s*r*1.7), 205, 335, fill=color, width=4)
    d.ellipse((cx-4, cy+s*.26-4, cx+4, cy+s*.26+4), fill=color)


def icon_radio(cx, cy, s, color):
    rr((cx-s*.4, cy-s*.26, cx+s*.4, cy+s*.3), 8, None, color, 4)
    d.ellipse((cx-s*.24, cy-s*.02, cx-s*.06, cy+s*.16), outline=color, width=4)
    line([(cx+s*.06, cy-s*.08), (cx+s*.28, cy-s*.08)], color, 4)
    line([(cx+s*.06, cy+s*.06), (cx+s*.28, cy+s*.06)], color, 4)


icons = {
    "home": icon_home, "radio": icon_radio, "media": icon_music,
    "phone": icon_phone, "nav": icon_nav, "car": icon_car,
    "settings": icon_gear, "carplay": icon_carplay,
}

# Left navigation rail
rail_w = 104
d.rectangle((0, 0, rail_w, H), fill="#0b0b0c")
d.line((rail_w, 0, rail_w, H), fill=LINE, width=1)
nav = [("home", 92), ("carplay", 194), ("car", 296), ("settings", 398)]
for name, cy in nav:
    if name == "home":
        rr((18, cy-38, 86, cy+38), 13, PANEL_HOVER)
        d.rectangle((0, cy-24, 4, cy+24), fill=RED)
    icons[name](52, cy, 46, TEXT if name == "home" else MUTED)

# Power glyph at bottom
d.arc((34, 638, 70, 674), 45, 315, fill="#6d6d72", width=4)
line([(52, 632), (52, 652)], "#6d6d72", 4)

# Header
d.text((142, 31), "Startseite", font=font(29, True), fill=TEXT)
d.text((142, 69), "Audi MMI", font=font(16), fill=MUTED)
d.text((1428, 35), "18:42", font=font(24, True), fill=TEXT)
d.ellipse((1395, 47, 1404, 56), fill="#54c96b")
d.text((1325, 38), "CarPlay", font=font(15), fill=MUTED)
d.line((126, 108, 1570, 108), fill=LINE, width=1)

# 4x2 function grid
left, top = 128, 128
gap_x, gap_y = 12, 12
tw = (W-left-30-gap_x*3)//4
th = (H-top-28-gap_y)//2
tiles = [
    ("radio", "Radio", "#df3545"),
    ("media", "Media", "#9e73d4"),
    ("phone", "Telefon", "#38a9d4"),
    ("nav", "Navigation", "#e15b35"),
    ("carplay", "Apple CarPlay", "#62bb56"),
    ("car", "Fahrzeug", "#e21b2d"),
    ("settings", "Einstellungen", "#a7a7ac"),
    ("home", "System", "#657d99"),
]
for idx, (name, label, accent) in enumerate(tiles):
    col, row = idx % 4, idx // 4
    x = left + col*(tw+gap_x)
    y = top + row*(th+gap_y)
    rr((x, y, x+tw, y+th), 12, PANEL, LINE, 1)
    icons[name](x+tw//2, y+th//2-23, 64, TEXT)
    d.text((x+22, y+th-51), label, font=font(18, True), fill=TEXT)
    d.rounded_rectangle((x+22, y+th-17, x+84, y+th-13), 2, fill=accent)

OUT.parent.mkdir(parents=True, exist_ok=True)
im.save(OUT)
print(OUT)
