#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


W, H = 1600, 720
ROOT = Path(__file__).parents[1]
OUT = Path(__file__).with_name("mmi-vehicle-settings-preview.png")


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


image = ImageOps.fit(
    Image.open(ROOT / "assets/alps-background.jpg").convert("RGB"),
    (W, H), Image.Resampling.LANCZOS, centering=(.5, .5),
).filter(ImageFilter.GaussianBlur(1.2)).convert("RGBA")
image = Image.blend(image, Image.new("RGBA", (W, H), (3, 3, 8, 255)), .40)
image = Image.alpha_composite(image, Image.new("RGBA", (W, H), (2, 2, 7, 92)))
draw = ImageDraw.Draw(image, "RGBA")

draw.rounded_rectangle((34, 22, 150, 68), 23, fill=(24, 24, 29, 242))
draw.text((92, 45), "‹  ZURÜCK", anchor="mm", font=font(14, True), fill="white")
draw.text((190, 29), "Fahrzeug", font=font(31, True), fill="white")
draw.text((190, 67), "Komfort · Wartung · Fahrzeugdaten", font=font(15), fill="#b2b2bd")
draw.rounded_rectangle((1162, 24, 1552, 76), 26, fill=(20, 20, 25, 242), outline="#6b1f29", width=2)
draw.ellipse((1186, 44, 1198, 56), fill="#db1c2e")
draw.text((1211, 42), "CAN getrennt · Änderungen gesperrt", font=font(15, True), fill="#e8e8ed")

cards = [
    ("Einparkhilfe", "CAN erforderlich", "#c21424"),
    ("Ölstand", "Messwert noch nicht verfügbar", "#b74012"),
    ("Serviceintervall", "Messwert noch nicht verfügbar", "#3b6baa"),
    ("Scheibenwischer", "Änderungen gesperrt", "#1f7587"),
    ("Kombiinstrument", "Änderungen gesperrt", "#61389e"),
    ("Außenbeleuchtung", "Änderungen gesperrt", "#b75912"),
    ("Fenster", "Änderungen gesperrt", "#1a6dab"),
    ("Zentralverriegelung", "Änderungen gesperrt", "#911a2b"),
    ("Fahrzeug-ID-Nummer", "Noch nicht ausgelesen", "#4c525e"),
]
for i, (title, status, accent) in enumerate(cards):
    col, row = i % 3, i // 3
    x, y = 42 + col * 519, 116 + row * 174
    draw.rounded_rectangle((x, y, x + 493, y + 143), 18, fill=(12, 13, 16, 234), outline="#50525c", width=2)
    draw.rounded_rectangle((x, y, x + 7, y + 143), 4, fill=accent)
    draw.text((x + 27, y + 25), title, font=font(22, True), fill="white")
    draw.text((x + 27, y + 66), status, font=font(15), fill="#abadb7")
    draw.text((x + 466, y + 55), "›", anchor="mm", font=font(31), fill="#c7c8d0")

draw.text(
    (44, 683),
    "Die Menüs sind vollständig vorbereitet. Fahrzeugzugriffe werden nach dem CAN-Test einzeln freigeschaltet.",
    font=font(14), fill="#a8a8b2",
)
image.convert("RGB").save(OUT, quality=94)
print(OUT)
