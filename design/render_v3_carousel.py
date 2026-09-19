#!/usr/bin/env python3
"""Concept preview: expressive Audi-inspired launcher with a true carousel."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import math

W, H = 1600, 720
OUT = Path(__file__).with_name("mmi-v3-carousel-preview.png")


def fnt(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def gradient(size, top, bottom):
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(size[1]):
        t = y / max(1, size[1] - 1)
        c = tuple(round(top[i] * (1-t) + bottom[i] * t) for i in range(3))
        for x in range(size[0]):
            px[x, y] = c
    return img


photo_path = Path(__file__).parents[1] / "assets" / "alps-background.jpg"
if photo_path.exists():
    photo = Image.open(photo_path).convert("RGB")
    photo = ImageOps.fit(photo, (W, H), method=Image.Resampling.LANCZOS, centering=(0.5, 0.58))
    photo = photo.filter(ImageFilter.GaussianBlur(1.6)).convert("RGBA")
    # The photograph stays recognisable but never competes with labels/cards.
    photo = Image.blend(photo, Image.new("RGBA", (W, H), (2, 3, 7, 255)), 0.68)
    im = photo
else:
    im = gradient((W, H), (12, 12, 16), (3, 3, 5)).convert("RGBA")
d = ImageDraw.Draw(im)

# Colored light deliberately brings back the visual drama of older MMI menus.
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.ellipse((360, 50, 1240, 820), fill=(160, 0, 28, 80))
gd.ellipse((700, 110, 1660, 760), fill=(30, 30, 95, 40))
glow = glow.filter(ImageFilter.GaussianBlur(120))
im = Image.alpha_composite(im, glow)
d = ImageDraw.Draw(im)

# Header
d.text((42, 28), "AUDI MMI", font=fnt(18, True), fill="#e8e8eb")
d.text((800, 24), "Hauptmenü", anchor="ma", font=fnt(25, True), fill="#ffffff")
d.text((1518, 25), "18:42", anchor="ra", font=fnt(24, True), fill="#ffffff")
d.text((1432, 30), "18°C", anchor="ra", font=fnt(17, True), fill="#e7e7ea")
d.ellipse((1321, 37, 1331, 47), fill="#56d26f")
d.text((1302, 30), "CarPlay", anchor="ra", font=fnt(15), fill="#aaaaaf")
d.line((32, 72, 1568, 72), fill="#38383f", width=1)


def card(box, top, bottom, radius=24, outline="#404047", width=2):
    x1, y1, x2, y2 = box
    layer = gradient((x2-x1, y2-y1), top, bottom).convert("RGBA")
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, layer.width-1, layer.height-1), radius, fill=255)
    layer.putalpha(mask)
    im.alpha_composite(layer, (x1, y1))
    d.rounded_rectangle(box, radius, outline=outline, width=width)


def car_icon(cx, cy, scale, color="#ffffff"):
    pts = [(cx-scale*.46, cy+scale*.16), (cx-scale*.34, cy-scale*.18),
           (cx-scale*.2, cy-scale*.29), (cx+scale*.22, cy-scale*.29),
           (cx+scale*.38, cy-scale*.14), (cx+scale*.48, cy+scale*.16)]
    d.line(pts, fill=color, width=max(3, int(scale*.055)), joint="curve")
    d.line((cx-scale*.52, cy+scale*.16, cx+scale*.52, cy+scale*.16), fill=color, width=max(3, int(scale*.055)))
    d.ellipse((cx-scale*.33, cy+scale*.07, cx-scale*.13, cy+scale*.27), outline=color, width=max(3, int(scale*.045)))
    d.ellipse((cx+scale*.14, cy+scale*.07, cx+scale*.34, cy+scale*.27), outline=color, width=max(3, int(scale*.045)))


def note_icon(cx, cy, s):
    d.ellipse((cx-s*.42, cy+s*.15, cx-s*.1, cy+s*.47), outline="#ffffff", width=5)
    d.ellipse((cx+s*.1, cy+.02*s, cx+s*.42, cy+s*.34), outline="#ffffff", width=5)
    d.line((cx-s*.1, cy+s*.3, cx-s*.1, cy-s*.46, cx+s*.42, cy-s*.58, cx+s*.42, cy+s*.16), fill="#ffffff", width=5)


def carplay_icon(cx, cy, s):
    for r in (.22, .36, .50):
        d.arc((cx-s*r, cy-s*r*.55, cx+s*r, cy+s*r*1.45), 205, 335, fill="#ffffff", width=5)
    d.ellipse((cx-5, cy+s*.29-5, cx+5, cy+s*.29+5), fill="#ffffff")


# Outer cards remain visible and make the horizontal swipe behavior obvious.
card((-105, 195, 265, 555), (35, 17, 48), (10, 8, 15), 22, "#4a3855")
d.text((78, 234), "RADIO", anchor="ma", font=fnt(15, True), fill="#bcaec3")
d.text((78, 460), "Favoriten", anchor="ma", font=fnt(20, True), fill="#ffffff")

card((170, 152, 520, 600), (69, 30, 88), (18, 12, 24), 24, "#78548f")
d.text((345, 188), "MEDIA", anchor="ma", font=fnt(15, True), fill="#ceb9dc")
note_icon(345, 338, 82)
d.text((345, 494), "Deine Musik", anchor="ma", font=fnt(24, True), fill="#ffffff")
d.text((345, 530), "USB · Bluetooth", anchor="ma", font=fnt(15), fill="#c2b4c9")

# Selected center card
card((472, 112, 1128, 625), (112, 13, 32), (25, 8, 14), 28, "#d43a4f", 2)
d.text((520, 151), "FAHRZEUG", font=fnt(16, True), fill="#f1a1ad")
d.text((1080, 151), "1 / 8", anchor="ra", font=fnt(15), fill="#d98d98")

# subtle rings behind the vehicle
for r, alpha in ((178, "#5e2631"), (126, "#792b3a"), (78, "#963045")):
    d.ellipse((800-r, 330-r*.58, 800+r, 330+r*.58), outline=alpha, width=2)
car_icon(800, 330, 180)
d.text((800, 477), "Fahrzeug", anchor="ma", font=fnt(34, True), fill="#ffffff")
d.text((800, 520), "Verbrauch · Fahrzeugstatus · Service", anchor="ma", font=fnt(17), fill="#d7afb6")
d.rounded_rectangle((720, 563, 880, 603), 20, fill="#ffffff")
d.text((800, 582), "ÖFFNEN", anchor="mm", font=fnt(14, True), fill="#3b0710")

card((1080, 152, 1430, 600), (20, 76, 52), (8, 22, 17), 24, "#397b5f")
d.text((1255, 188), "PHONE APPS", anchor="ma", font=fnt(15, True), fill="#a6d1be")
carplay_icon(1255, 338, 82)
d.text((1255, 494), "Apple CarPlay", anchor="ma", font=fnt(24, True), fill="#ffffff")
d.text((1255, 530), "Bereit zum Verbinden", anchor="ma", font=fnt(15), fill="#a9c4b7")

card((1335, 195, 1705, 555), (17, 38, 75), (7, 11, 22), 22, "#314f7d")
d.text((1522, 234), "NAVIGATION", anchor="ma", font=fnt(15, True), fill="#9eb4d7")
d.text((1522, 460), "Karte", anchor="ma", font=fnt(20, True), fill="#ffffff")

# Carousel position and gestures
for i in range(8):
    x = 742 + i*17
    if i == 0:
        d.rounded_rectangle((x, 654, x+28, 660), 3, fill="#e21b2d")
    else:
        d.ellipse((x+10, 654, x+16, 660), fill="#6f6f76")
d.text((42, 657), "‹", font=fnt(36), fill="#b9b9bd")
d.text((1558, 657), "›", anchor="ra", font=fnt(36), fill="#b9b9bd")
d.text((800, 690), "Wischen oder antippen", anchor="ma", font=fnt(13), fill="#77777d")

im.convert("RGB").save(OUT)
print(OUT)
