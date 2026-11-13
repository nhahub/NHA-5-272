"""Original README graphics. Requires Pillow; no project data or database access.
Run from the repository root: python assets/readme/source/render_visuals.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
OUT=Path('assets/readme');OUT.mkdir(exist_ok=True)
NAVY='#071527';MID='#0B1E36';WHITE='#EAF4FF';CYAN='#00D4FF';TEAL='#00C9A7';PURPLE='#8B5CF6';MUTED='#AAC2D8';EDGE='#20405B'
FONT=Path('C:/Windows/Fonts')
def f(size,bold=False):return ImageFont.truetype(str(FONT/('seguisb.ttf' if bold else 'segoeui.ttf')),size)
def txt(d,xy,s,size=22,color=WHITE,bold=False):d.text(xy,s,font=f(size,bold),fill=color)
def base(w,h):
 im=Image.new('RGB',(w,h),NAVY);d=ImageDraw.Draw(im)
 for y in range(h):
  t=y/h;d.line((0,y,w,y),fill=(7+int(4*t),21+int(9*t),39+int(15*t)))
 for x in range(24,w,36):
  for y in range(24,h,36):d.ellipse((x,y,x+1,y+1),fill='#19324B')
 return im

def dot(d,x,y,c,r=5):
 d.ellipse((x-r-7,y-r-7,x+r+7,y+r+7),outline=EDGE,width=2);d.ellipse((x-r,y-r,x+r,y+r),fill=c)
def signal(d,a,b,t,c=CYAN):
 x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
 for r,co in [(8,EDGE),(5,c),(2,WHITE)]:d.ellipse((x-r,y-r,x+r,y+r),fill=co)
def save_anim(name,frames):
 frames[0].save(OUT/(name+'.png'),optimize=True)
 palette=frames[0].quantize(colors=128)
 q=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 q[0].save(OUT/(name+'.gif'),save_all=True,append_images=q[1:],duration=100,loop=0,optimize=True,disposal=1)
 print(name,(OUT/(name+'.gif')).stat().st_size)

def hero(mobile=False):
 w,h=(680,720) if mobile else (1200,560);frames=[]
 for k in range(40):
  im=base(w,h);d=ImageDraw.Draw(im)
  txt(d,(36,32),'DEPI  /  PROFESSIONAL DATA ANALYST TRACK',18 if mobile else 19,TEAL,True)
  txt(d,(36,93),'WIDE WORLD',54 if mobile else 64,WHITE,True);txt(d,(36,158),'IMPORTERS',54 if mobile else 64,WHITE,True)
  d.line((38,245,140,245),fill=CYAN,width=4)
  txt(d,(36,270),'Supply Chain Analytics',28 if mobile else 31,WHITE);txt(d,(36,310),'& Business Intelligence',28 if mobile else 31,WHITE)
  txt(d,(36,365),'From operational records',21,MUTED);txt(d,(36,395),'to connected business decisions.',21,MUTED)
  if mobile:
   nodes=[(70,560),(210,500),(340,590),(480,500),(610,560)];labs=['SOURCE','CLEAN','MODEL','ANALYZE','DECIDE'];ly=[600,462,630,462,600]
  else:
   nodes=[(750,160),(975,100),(1110,240),(930,335),(740,410)];labs=['SUPPLIERS','PURCHASING','INVENTORY','SALES','CUSTOMERS'];ly=[120,60,280,375,450]
  edges=[(0,1),(1,2),(2,3),(3,4),(4,0),(0,3),(1,3)]
  for j,(a,b) in enumerate(edges):d.line((*nodes[a],*nodes[b]),fill=EDGE,width=2);signal(d,nodes[a],nodes[b],(k/40+j*.19)%1,TEAL if j%2 else CYAN)
  for j,(x,y) in enumerate(nodes):
   dot(d,x,y,[CYAN,TEAL,PURPLE,CYAN,TEAL][j],10)
   d.ellipse((x-25,y-25,x+25,y+25),outline=[CYAN,TEAL,PURPLE,CYAN,TEAL][j],width=2)
   label=labs[j];tw=d.textlength(label,font=f(14,True));txt(d,(x-tw/2,ly[j]),label,14,MUTED,True)
  if not mobile:txt(d,(36,495),'SQL SERVER    /    PYTHON    /    ANALYTICAL VIEWS',17,MUTED)
  frames.append(im)
 save_anim('hero-mobile' if mobile else 'hero',frames)

def workflow(mobile=False):
 w,h=(640,1180) if mobile else (1200,610);frames=[]
 labels=[('Microsoft WWI','Full OLTP source'),('Bronze','Staged source snapshot'),('Python','Cleaning & transformation'),('Silver','Typed candidate tables'),('Gold','Analytical SQL views'),('Semantic model','Planned relationships'),('Power BI','Planned reporting'),('Business insights','Intended decision support')]
 for k in range(40):
  im=base(w,h);d=ImageDraw.Draw(im);txt(d,(30,24),'ONE TRACEABLE DATA JOURNEY',25 if mobile else 27,WHITE,True)
  txt(d,(30,65),'Solid: implemented layers  /  Dashed: planned reporting',18 if mobile else 20,MUTED)
  rects=[]
  for i,(a,b) in enumerate(labels):
   if mobile:x,y,cw,ch=32,116+i*126,576,102
   else:
    col=i if i<4 else 7-i;x,y,cw,ch=30+col*294,140+(0 if i<4 else 230),258,150
   rects.append((x,y,cw,ch))
  for i in range(7):
   x,y,cw,ch=rects[i];xx,yy,ww,hh=rects[i+1]
   if mobile:a=(x+cw/2,y+ch);b=(xx+ww/2,yy)
   elif i==3:a=(x+cw/2,y+ch);b=(xx+ww/2,yy)
   elif i<3:a=(x+cw,y+ch/2);b=(xx,yy+hh/2)
   else:a=(x,y+ch/2);b=(xx+ww,yy+hh/2)
   d.line((*a,*b),fill=EDGE,width=3);signal(d,a,b,(k/40+i*.14)%1,CYAN if i<4 else PURPLE)
  for i,(x,y,cw,ch) in enumerate(rects):
   color=TEAL if i<5 else PURPLE
   d.rounded_rectangle((x,y,x+cw,y+ch),radius=12,fill=MID,outline=color if i<5 else EDGE,width=2)
   if i>=5:
    for dx in range(x+12,x+cw-12,18):d.line((dx,y,dx+9,y),fill=PURPLE,width=2)
   txt(d,(x+16,y+12),f'{i+1:02}',18,color,True)
   txt(d,(x+60 if mobile else x+16,y+14 if mobile else y+48),labels[i][0],29 if mobile else 27,WHITE,True)
   txt(d,(x+60 if mobile else x+16,y+56 if mobile else y+98),labels[i][1],21 if mobile else 19,MUTED)
  if not mobile:txt(d,(30,560),'Tested locally in WWI_Cleaning_Test. Reporting architecture is proposed, not deployed.',19,MUTED)
  frames.append(im)
 save_anim('architecture-mobile' if mobile else 'architecture',frames)

def domains(mobile=False):
 w,h=(640,830) if mobile else (1200,420);frames=[]
 labels=['Sales performance','Customer analytics','Inventory intelligence','Purchasing & suppliers','Fulfillment efficiency']
 for k in range(40):
  im=base(w,h);d=ImageDraw.Draw(im);txt(d,(30,25),'FIVE LENSES. ONE SUPPLY CHAIN.',25 if mobile else 29,WHITE,True)
  txt(d,(30,68),'Conceptual illustrations — no measured business results',18,MUTED)
  for i,lab in enumerate(labels):
   if mobile:x,y,ww,hh=30,120+i*136,580,116
   else:x,y,ww,hh=30+i*234,140,216,230
   d.rounded_rectangle((x,y,x+ww,y+hh),radius=12,fill=MID,outline=EDGE,width=2)
   col=[CYAN,TEAL,PURPLE,TEAL,CYAN][i]
   gx,gy=(x+20,y+22) if mobile else (x+22,y+30)
   if i in [0,3]:
    for j,height in enumerate([24,43,33,65]):d.rounded_rectangle((gx+j*21,gy+70-height,gx+j*21+12,gy+70),radius=3,fill=col)
   elif i==1:
    for dx,dy in [(10,30),(75,5),(75,60)]:d.line((gx+10,gy+30,gx+dx,gy+dy),fill=EDGE,width=2);dot(d,gx+dx,gy+dy,col)
   elif i==2:
    for j in range(6):
     xx=gx+(j%3)*28;yy=gy+(j//3)*32;d.rectangle((xx,yy,xx+20,yy+23),outline=col,width=2)
   else:
    d.line((gx,gy+55,gx+25,gy+35,gx+55,gy+45,gx+85,gy+10),fill=col,width=3)
   signal(d,(gx,gy+80),(gx+85,gy+80),k/40,col)
   if mobile:txt(d,(x+140,y+40),lab,27,WHITE,True)
   else:
    words=lab.split(' ');txt(d,(x+18,y+144),words[0],24,WHITE,True);txt(d,(x+18,y+176),' '.join(words[1:]),20,MUTED)
  frames.append(im)
 save_anim('domains-mobile' if mobile else 'domains',frames)

def svg(name,w,h,body):
 (OUT/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img"><rect width="{w}" height="{h}" rx="16" fill="{NAVY}"/><g font-family="Segoe UI,Arial,sans-serif">{body}</g></svg>',encoding='utf-8')
def svgt(x,y,s,size=24,c=WHITE):return f'<text x="{x}" y="{y}" font-size="{size}" fill="{c}">{s}</text>'
def statics():
 b=svgt(30,48,'ENGINEERED TO BE CHECKED',28)+svgt(30,80,'Recorded isolated integration evidence · 13 November 2026',18,MUTED)
 for i,(n,s) in enumerate([('14','Cleaning components'),('31','Silver tables'),('18','Gold SQL views'),('80','Trusted foreign keys')]):
  x=30+(i%2)*300;y=115+(i//2)*130;b+=f'<rect x="{x}" y="{y}" width="280" height="112" rx="10" fill="{MID}" stroke="{EDGE}"/>'+svgt(x+18,y+51,n,42,CYAN)+svgt(x+18,y+85,s,21)
 b+=svgt(30,420,'1,057,452 candidate Silver rows',24,TEAL)+svgt(30,458,'SQL roundtrip · Metrics · Repeatability',21,MUTED)
 svg('validation',640,490,b)
 b=svgt(30,45,'GRAIN BEFORE AGGREGATION',27)+svgt(30,80,'Gold is a collection of SQL views',21,MUTED)
 rows=[('Order line','Ordered / picked / unmet units'),('Invoice line','Billed amounts / recorded profit'),('Purchase line','Packs / received units / expected value'),('Stock movement','Signed quantity per transaction')]
 for i,(a,c) in enumerate(rows):
  y=112+i*100;b+=f'<rect x="30" y="{y}" width="580" height="80" rx="10" fill="{MID}" stroke="{EDGE}"/>'+svgt(50,y+32,a,24,TEAL)+svgt(50,y+61,c,20)
 b+=svgt(30,550,'Join through keys. Keep distinct business grains.',22)+svgt(30,586,'Future dimensional / semantic model: subject to review.',18,MUTED)
 svg('model-grains',640,620,b)
for fn in [hero,workflow,domains]:
 fn(False);fn(True)
statics()
