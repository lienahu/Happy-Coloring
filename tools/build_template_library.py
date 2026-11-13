"""Build 30 local PNG templates and separate small thumbnails.
Original five PNGs are unchanged. New scenes combine those supplied originals
with original geometric SVG scenery. No external images, fonts or services.
Optional asset build dependencies: Pillow, scipy, numpy, cairosvg.
"""
from pathlib import Path
import math, json, base64, io
from PIL import Image
import numpy as np
from scipy import ndimage
import cairosvg
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/template-library';(OUT/'full').mkdir(parents=True,exist_ok=True);(OUT/'thumbs').mkdir(exist_ok=True)
class Drawing:
 def __init__(self): self.parts=[]
 def add(self,s): self.parts.append(s);return self
 def circle(self,x,y,r,fill='white',sw=6):return self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke-width="{sw}"/>')
 def ellipse(self,x,y,rx,ry,fill='white',sw=6):return self.add(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke-width="{sw}"/>')
 def path(self,d,fill='white',sw=6):return self.add(f'<path d="{d}" fill="{fill}" stroke-width="{sw}"/>')
 def rect(self,x,y,w,h,rx=0,fill='white',sw=6):return self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke-width="{sw}"/>')
 def group(self,s,x,y,scale=1,angle=0):return self.add(f'<g transform="translate({x},{y}) scale({scale}) rotate({angle})">{s}</g>')
 def png(self):
  svg='<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1200" viewBox="0 0 1200 1200"><rect width="1200" height="1200" fill="white"/><g stroke="#151515" stroke-linejoin="round" stroke-linecap="round">'+''.join(self.parts)+'</g></svg>'
  return cairosvg.svg2png(bytestring=svg.encode())
 def fragment(self):return ''.join(self.parts)
def star(x,y,r,points=5):
 p=[(x+math.cos(-math.pi/2+i*math.pi/points)*r*(1 if i%2==0 else .45),y+math.sin(-math.pi/2+i*math.pi/points)*r*(1 if i%2==0 else .45)) for i in range(points*2)]
 return 'M '+' L '.join(f'{a:.2f} {b:.2f}' for a,b in p)+' Z'
def cloud(d,x,y,s=1):d.group('<path d="M 0 45 C -30 45 -30 5 0 5 C 5 -38 68 -38 78 5 C 110 -22 154 3 145 32 C 183 62 143 85 112 70 L 10 70 C -16 70 -20 49 0 45 Z" fill="white"/>',x,y,s)
def flower(d,x,y,r=24,petals=6):
 for a in range(petals):
  t=a*2*math.pi/petals;d.ellipse(x+math.cos(t)*r*.8,y+math.sin(t)*r*.8,r*.55,r*.55,sw=4)
 d.circle(x,y,r*.4,sw=4)
def leaf(d,x,y,s=1,angle=0):d.group('<path d="M0 0 Q-36 -54 0 -90 Q36 -54 0 0Z" fill="white"/><path d="M0 0V-65" fill="none"/>',x,y,s,angle)
def plant(d,x,y,height=130):
 d.path(f'M{x} {y} L{x} {y-height}','none',5)
 for i in range(1,4):
  leaf(d,x,y-i*height/5,.48,-52 if i%2 else 52)
 flower(d,x,y-height,22)
def meadow(d,hard=False):
 d.path('M50 1000 Q300 915 540 1000 Q850 900 1150 1000 L1150 1150H50Z',sw=5)
 for x,y in [(110,1050),(240,1110),(1000,1095),(1100,1010),(880,1140)]:flower(d,x,y,22 if hard else 28)
 for x,y in [(90,950),(1120,925)]:plant(d,x,y,180 if hard else 120)
 if hard:
  for x,y in [(320,1090),(820,1110),(400,1140),(1040,940)]:leaf(d,x,y,.6,25)
def stars(d,hard=False):
 pts=[(125,180,30),(1010,115,35),(1070,390,23),(120,570,22),(930,720,24),(240,60,20)]
 if hard:pts += [(900,250,14),(330,170,16),(1050,960,21),(180,930,18),(700,85,18),(620,270,20),(300,760,18)]
 for x,y,r in pts:d.path(star(x,y,r),sw=4)
def border(d):
 d.rect(30,30,1140,1140,45,sw=5);d.rect(48,48,1104,1104,32,sw=3)
 for x in range(120,1150,100):
  d.path(star(x,70,12),sw=3);d.path(star(x,1130,12),sw=3)
 for y in range(170,1110,100):
  d.path('M0 -12 L10 0 L0 12 L-10 0Z',sw=3) if False else None
  for x in [70,1130]:d.path(f'M{x} {y-12}L{x+10} {y}L{x} {y+12}L{x-10} {y}Z',sw=3)
# Supplied characters: remove only exterior white connected to the image edge.
SPRITES={}
def character(d,name,x,y,w,h):
 if name not in SPRITES:
  im=Image.open(ROOT/f'assets/coloring-pages/{name}.png').convert('RGBA');a=np.array(im);white=(a[:,:,:3].min(axis=2)>240)
  seed=np.zeros_like(white);seed[0]=white[0];seed[-1]=white[-1];seed[:,0]=white[:,0];seed[:,-1]=white[:,-1]
  outside=ndimage.binary_propagation(seed,mask=white);a[outside,3]=0;im=Image.fromarray(a);im=im.crop(im.getbbox());buf=io.BytesIO();im.save(buf,format='PNG',optimize=True)
  SPRITES[name]=base64.b64encode(buf.getvalue()).decode()
 d.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{SPRITES[name]}" preserveAspectRatio="xMidYMid meet"/>')
def turtle(d,x=600,y=660,s=1,hard=False):
 q=Drawing();q.ellipse(-120,95,47,67);q.ellipse(100,100,45,65);q.ellipse(-120,-75,45,60);q.ellipse(100,-85,44,60);q.path('M-200 5 L-268 32 L-200 48Z');q.ellipse(0,0,220,165);q.ellipse(0,0,176,128)
 for a in [0,72,144,216,288]:
  t=math.radians(a);q.path(f'M0 0L{math.cos(t)*176:.1f} {math.sin(t)*128:.1f}','none',5)
 q.path('M-52 -60L50 -60L82 10L25 66L-55 42Z');q.ellipse(235,-5,85,77);q.circle(263,-22,10,'#151515');q.path('M240 30Q274 55 292 20','none')
 if hard:
  for a in range(0,360,30):q.circle(math.cos(math.radians(a))*195,math.sin(math.radians(a))*146,8,sw=3)
 d.group(q.fragment(),x,y,s)
def rocket(d,x=600,y=580,s=1,hard=False):
 q=Drawing();q.path('M-90 150L-158 230V95L-93 20Z');q.path('M90 150L158 230V95L93 20Z');q.path('M-60 220Q-80 320 0 360Q80 320 60 220Z');q.path('M-22 235Q-34 300 0 324Q34 300 22 235Z');q.path('M-90 225V-80Q-80 -220 0 -300Q80 -220 90 -80V225Z');q.path('M-75 -170Q0 -150 75 -170','none');q.rect(-90,170,180,55,8);q.circle(0,-45,63);q.circle(0,-45,44);q.path('M-28 -62Q-15 -80 8 -82','none',4);q.path(star(0,95,32),sw=4)
 if hard:
  for yy in [-130,150,193]:
   for xx in [-60,-30,0,30,60]:q.circle(xx,yy,3,'#151515',2)
 d.group(q.fragment(),x,y,s,-16)
def house(d,x,y,s=1,hard=False):
 q=Drawing();q.rect(-155,-50,310,290,16);q.path('M-190 -55L0 -240L190 -55Z');q.path('M-155 -50L0 -200L155 -50','none');q.rect(-47,98,94,142,28);q.circle(25,174,6);q.rect(-122,12,76,70,9);q.rect(48,12,76,70,9)
 for xx in [-84,86]:q.path(f'M{xx} 12V82M{xx-38} 47H{xx+38}','none',4)
 if hard:
  for yy in [-90,-125,-160]:q.path(f'M{-int((yy+240)*.82)} {yy}H{int((yy+240)*.82)}','none',3)
  for yy in [110,155,200]:
   for xx in [-128,-93,80,115]:q.rect(xx,yy,28,17,2,sw=3)
 d.group(q.fragment(),x,y,s)
def fish(d,x,y,s=1,hard=False):
 q=Drawing();q.path('M-130 0L-240 -110Q-215 0 -240 110Z');q.path('M-40 -90Q45 -180 95 -62Z');q.path('M0 92Q75 170 110 52Z');q.ellipse(0,0,170,105);q.path('M95 -86Q35 0 95 86','none');q.circle(113,-28,16,'#151515');q.circle(118,-34,5,'white',0);q.path('M122 35Q148 48 157 22','none',4);q.path('M-8 -30Q-60 -60 -68 0Q-60 60 -8 30Z')
 if hard:
  for yy in [-65,0,65]:
   for xx in [-110,-65,-20]:q.path(f'M{xx} {yy-20}Q{xx+38} {yy} {xx} {yy+20}','none',3)
 d.group(q.fragment(),x,y,s)
def cupcake(d,x,y,s=1,hard=False):
 q=Drawing();q.path('M-150 -20L-110 200H110L150 -20Z');q.path('M-155 -20C-210 -65 -165 -130 -110 -135C-150 -200 -70 -220 -35 -210C-45 -265 45 -270 65 -205C140 -225 170 -160 130 -125C210 -105 205 -35 155 -20Z');q.circle(15,-266,30);q.path('M15 -295Q15 -335 45 -339','none')
 for xx in [-90,-45,0,45,90]:q.path(f'M{xx} 20L{xx*.75} 175','none',5)
 if hard:
  for xx,yy in [(-100,-70),(-50,-110),(10,-90),(80,-65),(75,-155),(-50,-180)]:q.path(star(xx,yy,12),sw=3)
 d.group(q.fragment(),x,y,s)
def balloon(d,x,y,s=1,hard=False):
 q=Drawing();q.path('M-175 -40C-270 -330 270 -330 175 -40Q130 35 65 90H-65Q-130 35 -175 -40Z');q.path('M-65 90C-205 -135 -100 -270 0 -270C100 -270 205 -135 65 90','none');q.path('M-22 90C-65 -90 -60 -200 0 -270C60 -200 65 -90 22 90','none');q.path('M-65 90L-60 190M65 90L60 190','none');q.rect(-72,190,144,100,18)
 if hard:
  for yy in [215,240,265]:q.path(f'M-66 {yy}H66','none',3)
  for xx in [-42,-14,14,42]:q.path(f'M{xx} 195V285','none',3)
 d.group(q.fragment(),x,y,s)
def castle(d,x,y,s=1,hard=False):
 q=Drawing()
 for xx,ht in [(-250,330),(0,470),(250,330)]:
  q.rect(xx-72,-ht,144,ht+160,5);q.path(f'M{xx-98} {-ht}L{xx} {-ht-130}L{xx+98} {-ht}Z');q.path(f'M{xx} {-ht-130}V{-ht-205}L{xx+65} {-ht-179}L{xx} {-ht-155}','none',4)
  for yy in range(-ht+55,80,90):q.rect(xx-22,yy,44,58,21,sw=5)
 q.rect(-245,-50,490,240,8);q.path('M-65 190V65Q0 -15 65 65V190Z')
 for xx in [-220,-160,-100,80,140,200]:q.rect(xx,-83,38,42,3)
 if hard:
  for yy in [8,65,123]:
   for xx in [-220,-155,105,170]:q.rect(xx,yy,44,27,2,sw=3)
 d.group(q.fragment(),x,y,s)
def planet(d,x,y,r,ring=False):
 d.circle(x,y,r,sw=5)
 if ring:d.add(f'<ellipse cx="{x}" cy="{y}" rx="{r*1.7}" ry="{r*.3}" transform="rotate(-20 {x} {y})" fill="white" stroke-width="5"/>')
 else:
  d.circle(x-r*.3,y-r*.3,r*.22,sw=4);d.circle(x+r*.4,y+r*.3,r*.14,sw=3)
def coral(d,x,y,s=1):d.group('<path d="M-12 0V-60C-70 -75 -70 -135 -50 -140Q-30 -145 -35 -100L-10 -88V-170Q0 -195 12 -170V-105L40 -120V-160Q60 -180 65 -150V-105Q52 -70 12 -65V0Z" fill="white"/>',x,y,s)
def owl(d,x,y,s=1):
 q=Drawing();q.path('M-170 -130L-170 -230L-60 -175Q0 -195 60 -175L170 -230L170 -130C270 130 130 230 0 230C-130 230 -270 130 -170 -130Z');q.ellipse(-75,-65,85,100);q.ellipse(75,-65,85,100)
 for xx in [-75,75]:q.circle(xx,-70,24,'#151515');q.circle(xx+8,-80,8,'white',0)
 q.path('M-25 10L0 50L25 10Z');q.path('M-170 -45Q-80 80 -148 175','none');q.path('M170 -45Q80 80 148 175','none')
 for yy in [80,125,170]:
  for xx in [-60,0,60]:q.path(f'M{xx-18} {yy-10}Q{xx} {yy+20} {xx+18} {yy-10}','none',4)
 d.group(q.fragment(),x,y,s)

def build(kind,hard=False):
 d=Drawing()
 if hard:border(d)
 if kind=='turtle':turtle(d,560,620,1.5);flower(d,940,970,40)
 elif kind=='rocket':stars(d);rocket(d,620,625,1.25);planet(d,230,300,95)
 elif kind=='house':cloud(d,170,170,1.5);cloud(d,850,220,1.1);house(d,610,690,1.6);flower(d,230,1050,34);flower(d,980,1050,34)
 elif kind=='fish':fish(d,650,650,1.7);[d.circle(x,y,r) for x,y,r in [(920,340,28),(1010,220,18),(1080,125,12)]]
 elif kind=='cupcake':cupcake(d,600,670,1.7);[d.path(star(x,y,32)) for x,y in [(180,250),(1000,370),(170,930)]]
 elif kind=='balloon':balloon(d,600,610,1.5);cloud(d,100,740,1.3);cloud(d,900,320,1.2)
 elif kind=='garden-kitten':
  cloud(d,220,130,1.3);d.circle(960,180,70);meadow(d);character(d,'cat',240,310,710,780)
 elif kind=='butterfly-meadow':
  for x in [180,1010]:plant(d,x,1100,260);cloud(d,120,100,.8);character(d,'butterfly',240,170,720,850)
 elif kind=='dino-volcano':
  d.path('M100 550L340 160L570 550Z');d.path('M270 280L340 160L410 280L375 260L343 290L310 250Z');cloud(d,300,100,.7);cloud(d,860,150,1);meadow(d);character(d,'dinosaur',140,350,960,730)
 elif kind=='princess-castle':
  castle(d,600,590,.70);cloud(d,110,190,.9);cloud(d,950,150,.9);meadow(d);character(d,'princess',330,430,540,710)
 elif kind=='turtle-pond':
  d.ellipse(600,700,510,360);d.ellipse(600,700,465,310,'none',3);turtle(d,570,700,1.25);cloud(d,220,150,1);d.circle(1000,160,60)
  for x,y in [(270,1000),(970,880),(940,450)]:d.ellipse(x,y,90,36);flower(d,x,y-20,33)
 elif kind=='rocket-moon':stars(d,True);planet(d,230,240,120,True);planet(d,900,900,140);rocket(d,650,600,1.2)
 elif kind=='boat':
  d.path('M140 840Q380 790 600 840T1060 840V1140H140Z');d.path('M210 775H1030L875 985H365Z');d.path('M580 160V775','none',9);d.path('M555 200L250 720H555Z');d.path('M610 290L1000 720H610Z');d.path('M580 160V95L710 130L580 160Z');cloud(d,160,190,1.2);d.circle(1010,170,65)
  for xx in [420,600,780]:d.circle(xx,853,31)
 elif kind=='cottage-garden':
  cloud(d,180,180,1);house(d,600,650,1.25,True);d.path('M545 950L400 1160H800L655 950Z');meadow(d)
  for xx in [180,1010]:plant(d,xx,1080,250)
 elif kind=='birthday-cake':
  d.ellipse(600,1000,445,60);d.rect(230,650,740,340,45);d.rect(325,430,550,235,35)
  for xx in [410,600,790]:d.rect(xx-18,290,36,140,8);d.path(f'M{xx} 290Q{xx-55} 245 {xx} 190Q{xx+55} 245 {xx} 290Z')
  for xx in range(295,950,100):d.path(f'M{xx} 700Q{xx+50} 800 {xx+100} 700','none');flower(d,600,540,40)
 elif kind=='unicorn-garden':
  castle(d,900,400,.48,True);cloud(d,160,170,.8);stars(d,True);meadow(d,True);character(d,'unicorn',180,300,820,790)
  for xx in [130,1060]:plant(d,xx,1020,300)
 elif kind=='palace-princess':
  castle(d,600,635,.76,True);meadow(d,True);character(d,'princess',375,490,470,610)
  for xx in [210,980]:plant(d,xx,1000,235)
 elif kind=='cats-greenhouse':
  d.path('M160 1030V370L600 110L1040 370V1030Z');d.path('M160 370H1040M600 110V1030M380 240V1030M820 240V1030M160 650H1040','none',5)
  for xx in [240,960]:d.rect(xx-70,875,140,135,13);plant(d,xx,875,260)
  character(d,'cat',260,620,350,430);character(d,'cat',610,665,315,390)
  flower(d,600,330,70);flower(d,390,440,40);flower(d,820,440,40)
 elif kind=='butterfly-mandala':
  for r in [500,455,385]:d.circle(600,600,r,'none',4)
  for a in range(0,360,30):
   t=math.radians(a);x=600+math.cos(t)*430;y=600+math.sin(t)*430;flower(d,x,y,25);d.path(star(600+math.cos(t)*485,600+math.sin(t)*485,15),sw=3)
  character(d,'butterfly',300,260,600,680)
 elif kind=='dinosaur-valley':
  d.path('M80 550L310 130L560 550Z');d.path('M570 550L870 170L1130 550Z');cloud(d,280,100,.7);cloud(d,850,160,.7);meadow(d,True)
  character(d,'dinosaur',120,465,620,600);character(d,'dinosaur',720,650,330,380)
  for xx,yy in [(120,610),(1030,560)]:plant(d,xx,yy,210)
  for xx in [300,500,870]:d.ellipse(xx,1080,35,50)
 elif kind=='coral-reef':
  for xx,yy,ss in [(160,1080,1.3),(330,1140,.8),(900,1100,1.4),(1030,940,.8)]:coral(d,xx,yy,ss)
  fish(d,470,440,1.3,True);fish(d,820,790,.8,True);turtle(d,860,290,.58,True)
  for xx,yy,rr in [(170,300,17),(215,190,11),(950,660,25),(1040,540,18),(650,870,13)]:d.circle(xx,yy,rr,sw=4)
  for xx,yy in [(560,1050),(760,1120),(150,780)]:d.path(star(xx,yy,42),sw=4)
 elif kind=='space-adventure':
  stars(d,True);planet(d,240,260,120,True);planet(d,945,320,115);planet(d,780,965,130);rocket(d,570,680,1.05,True)
  d.rect(100,700,140,90,15);d.rect(65,730,35,35,3);d.rect(240,730,35,35,3);d.path('M170 700V650M145 650H195','none',5)
  for xx in [120,165,210]:d.rect(xx,720,22,24,3,sw=3)
 elif kind=='fairy-village':
  cloud(d,220,170,1.1);cloud(d,900,130,.8);d.circle(680,190,60);d.path('M110 1140Q370 800 600 840Q900 720 1090 1100','none')
  house(d,330,520,.75,True);house(d,850,560,.72,True);house(d,600,900,.7,True)
  for xx,yy in [(150,900),(1030,1000),(600,440)]:plant(d,xx,yy,170)
  flower(d,350,1040,28);flower(d,900,800,28)
 elif kind=='sweet-shop':
  d.rect(155,190,890,890,24);d.rect(130,155,940,170,25)
  for xx in range(150,1030,80):d.rect(xx,158,42,163,5,sw=4)
  d.rect(190,375,820,610,18);d.path('M200 690H1000','none',8);cupcake(d,420,560,.52,True);cupcake(d,780,550,.52,True)
  for xx in [330,600,870]:d.circle(xx,845,80);d.circle(xx,845,27);[d.path(star(xx+math.cos(a)*53,845+math.sin(a)*53,7),sw=2) for a in [0,1.2,2.4,3.6,4.8]]
 elif kind=='woodland-owl':
  d.path('M140 1030Q600 930 1060 1030L1060 1080Q600 980 140 1080Z');owl(d,600,670,1.3)
  d.circle(900,180,70);stars(d)
  for xx in [160,1040]:
   d.path(f'M{xx} 1030Q{xx-50} 600 {xx} 240','none',7)
   for yy in [300,450,600,750]:leaf(d,xx,yy,.8,-60 if xx<600 else 60);leaf(d,xx,yy+70,.65,60 if xx<600 else -60)
 return d

# ID, level, artwork builder/original, seven translated titles.
rows=[
('kitten','easy','@cat',['Smiling kitten','Petit chat','Gatinho','Gatito','微笑小猫','にっこりねこ','웃는 고양이']),
('butterfly','easy','@butterfly',['Butterfly','Papillon','Borboleta','Mariposa','蝴蝶','ちょうちょ','나비']),
('dinosaur','easy','@dinosaur',['Baby dinosaur','Bébé dinosaure','Dinossauro bebé','Dinosaurio bebé','小恐龙','あかちゃん恐竜','아기 공룡']),
('princess','easy','@princess',['Little princess','Petite princesse','Princesinha','Princesita','小公主','小さなプリンセス','작은 공주']),
('turtle','easy','turtle',['Friendly turtle','Gentille tortue','Tartaruga simpática','Tortuga amable','小乌龟','やさしいかめ','친절한 거북이']),
('rocket','easy','rocket',['Little rocket','Petite fusée','Foguetão','Cohete','小火箭','小さなロケット','작은 로켓']),
('house','easy','house',['Cozy house','Jolie maison','Casinha','Casita','温馨小屋','かわいいおうち','아늑한 집']),
('fish','easy','fish',['Happy fish','Poisson joyeux','Peixinho feliz','Pez feliz','快乐小鱼','にこにこさかな','행복한 물고기']),
('cupcake','easy','cupcake',['Cupcake','Petit gâteau','Queque','Magdalena','杯子蛋糕','カップケーキ','컵케이크']),
('balloon','easy','balloon',['Hot-air balloon','Montgolfière','Balão de ar quente','Globo aerostático','热气球','気球','열기구']),
('rainbow-unicorn','medium','@unicorn',['Rainbow unicorn','Licorne arc-en-ciel','Unicórnio e arco-íris','Unicornio y arcoíris','彩虹独角兽','虹のユニコーン','무지개 유니콘']),
('garden-kitten','medium','garden-kitten',['Kitten garden','Chat au jardin','Gatinho no jardim','Gatito en el jardín','花园小猫','お庭のこねこ','정원의 고양이']),
('butterfly-meadow','medium','butterfly-meadow',['Butterfly meadow','Prairie aux papillons','Prado de borboletas','Prado de mariposas','蝴蝶花丛','花とちょうちょ','꽃밭의 나비']),
('dino-volcano','medium','dino-volcano',['Dinosaur volcano','Dinosaure et volcan','Dinossauro e vulcão','Dinosaurio y volcán','恐龙和火山','恐竜と火山','공룡과 화산']),
('princess-castle','medium','princess-castle',['Princess castle','Château de princesse','Castelo da princesa','Castillo de la princesa','公主城堡','プリンセスのお城','공주의 성']),
('turtle-pond','medium','turtle-pond',['Turtle pond','Étang des tortues','Lago das tartarugas','Estanque de tortugas','池塘乌龟','かめの池','거북이 연못']),
('rocket-moon','medium','rocket-moon',['Rocket and moon','Fusée et lune','Foguetão e lua','Cohete y luna','火箭与月亮','ロケットと月','로켓과 달']),
('boat','medium','boat',['Sailing boat','Voilier','Veleiro','Velero','小帆船','帆船','돛단배']),
('cottage-garden','medium','cottage-garden',['Cottage garden','Jardin du cottage','Jardim da casinha','Jardín de la casita','花园小屋','お花の家','정원 오두막']),
('birthday-cake','medium','birthday-cake',['Birthday cake','Gâteau de fête','Bolo de aniversário','Tarta de cumpleaños','生日蛋糕','お誕生日ケーキ','생일 케이크']),
('unicorn-garden','hard','unicorn-garden',['Magic unicorn garden','Jardin des licornes','Jardim mágico','Jardín de unicornios','独角兽魔法花园','ユニコーンの庭','유니콘 마법 정원']),
('palace-princess','hard','palace-princess',['Royal palace','Palais royal','Palácio real','Palacio real','公主的宫殿','プリンセスの宮殿','공주의 궁전']),
('cats-greenhouse','hard','cats-greenhouse',['Cats in a greenhouse','Chats dans la serre','Gatos na estufa','Gatos en el invernadero','温室里的小猫','温室のこねこたち','온실 속 고양이']),
('butterfly-mandala','hard','butterfly-mandala',['Butterfly wreath','Couronne de papillons','Grinalda de borboletas','Corona de mariposas','蝴蝶花环','ちょうちょの花輪','나비 꽃장식']),
('dinosaur-valley','hard','dinosaur-valley',['Dinosaur valley','Vallée des dinosaures','Vale dos dinossauros','Valle de dinosaurios','恐龙山谷','恐竜の谷','공룡 계곡']),
('coral-reef','hard','coral-reef',['Coral reef','Récif de corail','Recife de coral','Arrecife de coral','珊瑚海底世界','さんごの海','산호 바다']),
('space-adventure','hard','space-adventure',['Space adventure','Aventure spatiale','Aventura espacial','Aventura espacial','太空探险','宇宙の冒険','우주 탐험']),
('fairy-village','hard','fairy-village',['Fairy village','Village féerique','Aldeia encantada','Pueblo de hadas','童话村庄','おとぎの村','동화 마을']),
('sweet-shop','hard','sweet-shop',['Sweet shop','Boutique de douceurs','Loja de doces','Tienda de dulces','甜点小店','おかしのお店','과자 가게']),
('woodland-owl','hard','woodland-owl',['Woodland owl','Hibou de la forêt','Coruja da floresta','Búho del bosque','森林猫头鹰','森のふくろう','숲속 부엉이'])]
locales=['en','fr','pt','es','zh-Hans','ja','ko'];items=[];probes={}
for name,level,kind,titles in rows:
 id=f'{level}-{name}'
 if kind.startswith('@'):src=f'assets/coloring-pages/{kind[1:]}.png';provenance='supplied-original'
 else:
  src=f'assets/template-library/full/{id}.png';raw=build(kind,level=='hard').png();im=Image.open(io.BytesIO(raw)).convert('RGB');im.save(ROOT/src,optimize=True);provenance='original-vector-scene-with-supplied-character' if any(x in kind for x in ['kitten','unicorn','princess','butterfly','dino','cats']) else 'original-vector-scene'
 im=Image.open(ROOT/src).convert('RGB');thumb=f'assets/template-library/thumbs/{id}.png';small=im.copy();small.thumbnail((192,192));small.save(ROOT/thumb,optimize=True)
 items.append(dict(id=id,level=level,title=dict(zip(locales,titles)),src=src,thumb=thumb,width=im.width,height=im.height,provenance=provenance))
 # Pixel probe in the largest interior connected white region, for asset smoke tests.
 arr=np.asarray(im.convert('L'));labels,n=ndimage.label(arr>210);edges=set(np.r_[labels[0],labels[-1],labels[:,0],labels[:,-1]]);counts=np.bincount(labels.ravel());interior=[v for v in range(1,n+1) if v not in edges and counts[v]>80]
 if not interior:raise RuntimeError(f'{id}: no closed region')
 top=max(interior,key=lambda v:counts[v]);dist=ndimage.distance_transform_edt(labels==top);yy,xx=np.unravel_index(dist.argmax(),dist.shape);probes[id]=dict(x=xx/im.width,y=yy/im.height,closedRegions=len(interior),maxInterior=int(counts[top]))
 print(id,im.size,'closed regions',len(interior),'size',round((ROOT/src).stat().st_size/1024))
(OUT/'catalog.json').write_text(json.dumps(dict(version=1,pageSize=6,items=items),ensure_ascii=False,indent=2))
(ROOT/'tests/fixtures/library-probes.json').write_text(json.dumps(probes,indent=2))
print('Total',len(items),'catalog entries')
