#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

W,H=1600,720
root=Path(__file__).parents[1]
out=Path(__file__).with_name('mmi-settings-preview.png')

def font(size,bold=False):
    for p in ['/System/Library/Fonts/SFNS.ttf','/System/Library/Fonts/SFNSDisplay.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']:
        try:return ImageFont.truetype(p,size)
        except OSError:pass
    return ImageFont.load_default()

im=ImageOps.fit(Image.open(root/'assets/alps-background.jpg').convert('RGB'),(W,H),Image.Resampling.LANCZOS,centering=(.5,.5)).filter(ImageFilter.GaussianBlur(1.2)).convert('RGBA')
im=Image.blend(im,Image.new('RGBA',(W,H),(3,3,8,255)),.57)
d=ImageDraw.Draw(im,'RGBA')
d.rectangle((0,0,W,H),fill=(2,2,7,100))
d.rounded_rectangle((34,22,150,68),23,fill=(24,24,29,242))
d.text((92,45),'‹  ZURÜCK',anchor='mm',font=font(14,True),fill='white')
d.text((190,29),'Einstellungen',font=font(31,True),fill='white')
d.text((190,67),'Display · Audio · CarPlay · Fahrzeug',font=font(15),fill='#b2b2bd')
cards=[('Audio','Lautstärke  50 %','#a61429'),('Display','Helligkeit  80 %','#195cad'),('Darstellung','Auto','#6d33b2'),('Bildschirm aus','Nie','#2b7385'),('Startansicht','Hauptmenü','#197a4c'),('Animationen','Ein','#b25714'),('Tastentöne','Aus','#733f2e'),('Alpen-Hintergrund','68 %','#5c616b'),('Verbindungen','WLAN · Bluetooth','#145e9e'),('Apple CarPlay','Dongle- und Audiostatus','#147a45'),('Fahrzeug & CAN','Hardware noch nicht verbunden','#ad101f'),('System','Temperatur · Speicher · Updates','#484c57')]
for i,(title,value,color) in enumerate(cards):
    col,row=i%4,i//4
    x,y=42+col*389,116+row*174
    d.rounded_rectangle((x,y,x+363,y+143),17,fill=(14,15,18,232),outline='#595a64',width=2)
    d.text((x+24,y+20),title,font=font(15,True),fill='#afb0ba')
    value_size=18 if len(value)>27 else 20 if len(value)>20 else 23
    d.text((x+24,y+55),value,font=font(value_size,True),fill='white')
    d.ellipse((x+328,y+65,x+340,y+77),fill=color)
d.text((44,683),'Alle Pi-Einstellungen bleiben gespeichert. Fahrzeugfunktionen werden nach dem CAN-Test freigeschaltet.',font=font(14),fill='#a0a0aa')
im.convert('RGB').save(out,quality=94)
print(out)
