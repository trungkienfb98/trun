#!/usr/bin/env python3
"""autoedit.py – dựng video nói chuyện (talking-head) kiểu TikTok/Reels tự động.

Lệnh:
  prep    <plan.json>   video 1080p trung gian + voice.wav
  align   <plan.json>   khớp các câu thoại (plan.lines) vào thời gian -> work/lines.json
  cuts    <plan.json>   tính các đoạn giữ lại sau khi cắt khoảng lặng -> work/keep.json
  preview <plan.json>   ảnh xem trước toàn bộ tiêu đề + ảnh trám -> work/preview.jpg
  render  <plan.json>   âm thanh (nhạc, SFX, ducking) + hình + nén -> plan.output
Cần: ffmpeg, python3, numpy, scipy, pillow.
"""
import json, math, os, random, subprocess, sys, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS, SR = 1080, 1920, 30, 48000

# ======================================================================
# Cấu hình & tiện ích
# ======================================================================
def load(plan_path):
    plan = json.load(open(plan_path))
    plan.setdefault('work', os.path.join(os.path.dirname(os.path.abspath(plan_path)), 'work'))
    os.makedirs(plan['work'], exist_ok=True)
    return plan

def wp(plan, name): return os.path.join(plan['work'], name)

def run(cmd):
    subprocess.run(cmd, check=True)

def find_font(cands, fc):
    for p in cands:
        if os.path.exists(p): return p
    try:
        p = subprocess.run(['fc-match', '-f', '%{file}', fc], capture_output=True, text=True).stdout.strip()
        if p: return p
    except Exception:
        pass
    return '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

FONTS = {
    # chữ viết tay
    'script': find_font(['/usr/share/fonts/truetype/google-fonts/GreatVibes-Regular.ttf',
                         '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf'], 'TeX Gyre Chorus'),
    # chữ đậm cô đặc (kiểu Oswald)
    'bold': find_font(['/usr/share/fonts/truetype/google-fonts/Oswald-Bold.ttf',
                       '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf'], 'TeX Gyre Heros Cn:bold'),
    # chữ đen rất đậm
    'black': find_font(['/usr/share/fonts/opentype/inter/Inter-Black.otf'], 'Inter:black'),
    # chữ có chân đậm
    'serif': find_font(['/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf'], 'Lora:bold'),
}
SERIF_VAR = 'Bold'

COLORS = {   # (màu chữ, màu phát sáng)
    'orange': ('#fff3ea', '#ff5a14'), 'blue': ('#eaf6ff', '#1e8cff'), 'cyan': ('#86f7ff', '#00c2ff'),
    'gold': (['#fff4c0', '#ffc21a', '#d97800'], '#ff8a00'), 'pink': (['#ffd0f0', '#ff6fc8', '#c13cff'], '#ff4fd8'),
    'purple': ('#efe8ff', '#8a5cff'), 'red': ('#fff0ea', '#ff2a2a'), 'green': (['#f4ffc8', '#a6e33c', '#4f9e12'], '#6fd12a'),
    'white': ('#ffffff', '#ffffff'), 'rainbow': (['#ffe08a', '#ff7a3d', '#e0408f', '#8a5cff'], '#ff6a3d'),
    'mint': ('#fbfff4', '#9fe870'), 'magenta': ('#ffe3f1', '#ff2f8a'),
}

def hexrgba(c, a=255):
    return (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), a)

def font(path, size):
    f = ImageFont.truetype(path, size)
    if path == FONTS['serif'] and 'Variable' in path:
        try: f.set_variation_by_name(SERIF_VAR)
        except Exception: pass
    return f

# ======================================================================
# Chữ phát sáng
# ======================================================================
def text_layer(text, fnt, fill, glow=None, glow_r=24, glow_gain=1.7, box=None):
    l, t, r, b = fnt.getbbox(text)
    tw, th = r - l, b - t
    pad = int(glow_r * 3 + 20 + (box['pad'] if box else 0))
    w, h = tw + 2 * pad, th + 2 * pad
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).text((pad - l, pad - t), text, font=fnt, fill=255)
    if isinstance(fill, list):
        grad = Image.new('RGBA', (1, th + 2))
        for y in range(th + 2):
            k = y / (th + 1) * (len(fill) - 1); i = min(int(k), len(fill) - 2); fr = k - i
            c0, c1 = hexrgba(fill[i]), hexrgba(fill[i + 1])
            grad.putpixel((0, y), tuple(int(c0[j] + (c1[j] - c0[j]) * fr) for j in range(4)))
        grad = grad.resize((w, th + 2))
        col = Image.new('RGBA', (w, h), (0, 0, 0, 0)); col.paste(grad, (0, pad - 1))
        col.putalpha(ImageChops.multiply(col.getchannel('A'), mask))
    else:
        col = Image.new('RGBA', (w, h), hexrgba(fill)); col.putalpha(mask)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if box:
        bx = Image.new('RGBA', (w, h), (0, 0, 0, 0)); p = box['pad']
        ImageDraw.Draw(bx).rounded_rectangle((pad - p, pad - p * 0.5, pad + tw + p, pad + th + p * 0.5), radius=box['r'], fill=hexrgba(box['fill']))
        out.alpha_composite(bx)
    # bóng tối mềm để chữ nổi trên nền sáng
    sh = mask.filter(ImageFilter.GaussianBlur(max(10, glow_r * 0.8))).point(lambda v: min(255, int(v * 1.6)))
    shl = Image.new('RGBA', (w, h), (10, 6, 2, 255)); shl.putalpha(sh.point(lambda v: int(v * 0.9)))
    out.alpha_composite(shl)
    if glow:
        gc, ga = glow if isinstance(glow, (tuple, list)) and not isinstance(glow, str) else (glow, 255)
        for rad, gain in ((glow_r, glow_gain), (glow_r * 0.35, 1.2)):
            g = mask.filter(ImageFilter.GaussianBlur(rad)).point(lambda v: min(255, int(v * gain * ga / 255)))
            gl = Image.new('RGBA', (w, h), hexrgba(gc)); gl.putalpha(g); out.alpha_composite(gl)
    out.alpha_composite(col)
    return out, tw

def make_layer(L):
    """L: {type: script|bold|black|serif|pill, text, x, y, size, color, align, maxw}"""
    typ = L.get('type', 'bold'); text = L['text']
    defaults = {'script': 96, 'bold': 140, 'black': 160, 'serif': 150, 'pill': 56}
    size = int(L.get('size', defaults.get(typ, 120)))
    maxw = L.get('maxw', 760 if typ == 'script' else 980)
    path = FONTS['black' if typ == 'pill' else typ]
    while True:
        f = font(path, size); l, t, r, b = f.getbbox(text)
        if r - l <= maxw or size < 30: break
        size = int(size * 0.94)
    if typ == 'script':
        img, tw = text_layer(text, f, '#ffffff', ('#ffffff', 150), 12)
    elif typ == 'pill':
        bg = L.get('box', '#ffd400'); ink = L.get('ink', '#1a1400')
        img, tw = text_layer(text, f, ink, None, 10, box=dict(pad=28, r=L.get('radius', 14), fill=bg))
    else:
        fill, glow = COLORS.get(L.get('color', 'orange'), COLORS['orange'])
        img, tw = text_layer(text, f, fill, glow, L.get('glow_r', 30 if typ != 'serif' else 28))
    return dict(img=img, x=L.get('x', 0), y=L.get('y', 0), tw=tw, align=L.get('align', 'center'))

def ease_out(p): return 1 - (1 - p) ** 3
def ease_back(p):
    c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))

def draw_titles(T, t, canvas):
    for ti in T:
        local = t - ti['start']
        if local < 0 or local > ti['dur']: continue
        outp = clamp((ti['dur'] - local) / 0.35)
        for i, ly in enumerate(ti['layers']):
            p = clamp((local - i * 0.12) / 0.6)
            if p <= 0: continue
            e = ease_out(p)
            alpha, sx, sy, dy, rot, blur = clamp(p * 1.8), 1.0, 1.0, 0.0, 0.0, (1 - outp) * 10
            a = ti['anim']
            if a == 'blur': blur += (1 - e) * 16; sx = sy = 1 + 0.12 * (1 - e)
            elif a == 'rise': dy = (1 - e) * 80
            elif a == 'swing': rot = (1 - e) * 14; sx = sy = 1 + 0.4 * (1 - e)
            elif a == 'pop': sx = sy = 0.3 + 0.7 * ease_back(p); alpha = clamp(p * 3)
            elif a == 'spread': sx = 1 + 0.35 * (1 - e); blur += (1 - e) * 8
            alpha *= outp
            if alpha <= 0.01: continue
            im = ly['img']
            if abs(sx - 1) > 0.002 or abs(sy - 1) > 0.002:
                im = im.resize((max(1, int(im.width * sx)), max(1, int(im.height * sy))), Image.BILINEAR)
            if abs(rot) > 0.05: im = im.rotate(rot, resample=Image.BILINEAR, expand=True)
            if blur > 0.4: im = im.filter(ImageFilter.GaussianBlur(blur))
            if alpha < 0.999:
                im = im.copy(); im.putalpha(im.getchannel('A').point(lambda v: int(v * alpha)))
            ax = ly['x']
            if ly['align'] == 'right': ax -= ly['tw'] * sx / 2
            elif ly['align'] == 'left': ax += ly['tw'] * sx / 2
            x = int(ti['cx'] + ax - im.width / 2); y = int(ti['cy'] + ly['y'] + dy - im.height / 2)
            canvas.alpha_composite(im, (max(0, x), max(0, y)), (max(0, -x), max(0, -y)))

# ======================================================================
# Ảnh trám đồ họa (neon)
# ======================================================================
ICX, ICY, S = 540, 760, 1080
def glowify(img, color, r=22, gain=2.2):
    a = img.getchannel('A').filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * gain)))
    g = Image.new('RGBA', img.size, hexrgba(color)); g.putalpha(a)
    out = Image.new('RGBA', img.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(img); return out
def br_background(color):
    bg = Image.new('RGBA', (W, H), (8, 10, 22, 255)); d = ImageDraw.Draw(bg)
    for y in range(0, H, 8):
        k = y / H; d.rectangle((0, y, W, y + 8), fill=(int(8 + 14 * k), int(10 + 4 * k), int(22 + 22 * k), 255))
    grid = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grid)
    for x in range(0, W + 1, 90): gd.line((x, 0, x, H), fill=(255, 255, 255, 14), width=2)
    for y in range(0, H + 1, 90): gd.line((0, y, W, y), fill=(255, 255, 255, 14), width=2)
    bg.alpha_composite(grid)
    halo = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(halo).ellipse((ICX - 420, ICY - 420, ICX + 420, ICY + 420), fill=hexrgba(color, 120))
    bg.alpha_composite(halo.filter(ImageFilter.GaussianBlur(160))); return bg
def cv():
    c = Image.new('RGBA', (S, S), (0, 0, 0, 0)); return c, ImageDraw.Draw(c)
def star(d, cx, cy, r, fill):
    pts = [(cx + (r if i % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + i * math.pi / 5),
            cy + (r if i % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
    d.polygon(pts, fill=fill)
LW = 16
def ic_shop():
    c, d = cv(); col = '#ff8a3d'
    d.rounded_rectangle((300, 420, 780, 900), 40, outline=hexrgba(col), width=LW)
    d.arc((410, 280, 670, 560), 180, 360, fill=hexrgba(col), width=LW)
    tag = Image.new('RGBA', (300, 170), (0, 0, 0, 0)); td = ImageDraw.Draw(tag)
    td.polygon([(0, 85), (60, 0), (300, 0), (300, 170), (60, 170)], fill=hexrgba('#ffd400'))
    td.ellipse((40, 70, 70, 100), fill=(20, 12, 0, 255))
    td.text((95, 38), 'SALE', font=ImageFont.truetype(FONTS['black'], 70), fill=(30, 18, 0, 255))
    c.alpha_composite(tag.rotate(-18, expand=True, resample=Image.BICUBIC), (600, 640)); return glowify(c, col)
def ic_mic():
    c, d = cv(); col = '#a07bff'
    d.rounded_rectangle((420, 230, 660, 640), 120, outline=hexrgba(col), width=LW)
    for y in range(320, 600, 50): d.line((450, y, 630, y), fill=hexrgba(col, 170), width=8)
    d.arc((350, 420, 730, 770), 0, 180, fill=hexrgba(col), width=LW)
    d.line((540, 770, 540, 880), fill=hexrgba(col), width=LW); d.line((430, 880, 650, 880), fill=hexrgba(col), width=LW)
    for k, r in enumerate((110, 170)):
        d.arc((310 - r, 435 - r, 310 + r, 435 + r), 135, 225, fill=hexrgba('#ffffff', 200 - 60 * k), width=10)
        d.arc((770 - r, 435 - r, 770 + r, 435 + r), -45, 45, fill=hexrgba('#ffffff', 200 - 60 * k), width=10)
    return glowify(c, col)
def ic_review():
    c, d = cv(); col = '#3fd8ff'
    d.polygon([(540, 420), (780, 530), (540, 640), (300, 530)], outline=hexrgba(col), width=LW)
    for seg in ((300, 530, 300, 820), (780, 530, 780, 820), (540, 640, 540, 930), (300, 820, 540, 930), (780, 820, 540, 930)):
        d.line(seg, fill=hexrgba(col), width=LW)
    for i in range(5): star(d, 300 + i * 120, 270, 52, hexrgba('#ffd400'))
    return glowify(c, col)
def ic_house():
    c, d = cv(); col = '#ffc21a'
    d.line((260, 560, 540, 300, 820, 560), fill=hexrgba(col), width=LW, joint='curve')
    d.rectangle((330, 520, 750, 900), outline=hexrgba(col), width=LW)
    d.rounded_rectangle((480, 690, 600, 900), 10, outline=hexrgba(col), width=LW)
    d.rectangle((380, 590, 450, 660), outline=hexrgba(col), width=10); d.rectangle((630, 590, 700, 660), outline=hexrgba(col), width=10)
    d.rectangle((660, 340, 720, 470), outline=hexrgba(col), width=12); return glowify(c, col)
def ic_car():
    c, d = cv(); col = '#ff4d4d'
    body = [(150, 700), (200, 600), (360, 570), (450, 470), (680, 470), (800, 580), (930, 610), (950, 720), (150, 720)]
    d.line(body + [body[0]], fill=hexrgba(col), width=LW, joint='curve')
    d.polygon([(470, 500), (560, 500), (560, 575), (395, 575)], outline=hexrgba(col, 220), width=10)
    d.polygon([(590, 500), (670, 500), (760, 575), (590, 575)], outline=hexrgba(col, 220), width=10)
    for x in (320, 780):
        d.ellipse((x - 85, 650, x + 85, 820), fill=(10, 10, 20, 255), outline=hexrgba(col), width=LW)
        d.ellipse((x - 30, 705, x + 30, 765), outline=hexrgba('#ffffff', 200), width=8)
    for k in range(3): d.line((60, 620 + k * 40, 130 - k * 20, 620 + k * 40), fill=hexrgba('#ffffff', 160), width=8)
    return glowify(c, col)
def ic_phone():
    c, d = cv(); col = '#ff2f8a'
    d.rounded_rectangle((370, 200, 710, 900), 50, outline=hexrgba(col), width=LW)
    d.rounded_rectangle((490, 230, 590, 255), 10, fill=hexrgba(col))
    d.polygon([(500, 470), (500, 630), (630, 550)], fill=hexrgba('#ffffff'))
    d.ellipse((440, 410, 640, 690), outline=hexrgba('#ffffff', 200), width=10)
    d.rounded_rectangle((420, 800, 660, 815), 7, fill=hexrgba('#ffffff', 90)); d.rounded_rectangle((420, 800, 560, 815), 7, fill=hexrgba('#00e5ff'))
    return glowify(c, col)
def ic_ai():
    c, d = cv(); col = '#3fd8ff'
    layers = [[(250, y) for y in (330, 500, 670, 840)], [(540, y) for y in (420, 585, 750)], [(830, y) for y in (330, 500, 670, 840)]]
    for a, b in ((0, 1), (1, 2)):
        for p in layers[a]:
            for q in layers[b]: d.line(p + q, fill=hexrgba(col, 90), width=5)
    for Lr in layers:
        for x, y in Lr: d.ellipse((x - 34, y - 34, x + 34, y + 34), fill=(8, 12, 30, 255), outline=hexrgba(col), width=10)
    d.rounded_rectangle((430, 500, 650, 670), 26, fill=(8, 12, 30, 255), outline=hexrgba('#ffffff'), width=12)
    d.text((540, 585), 'AI', font=ImageFont.truetype(FONTS['black'], 110), fill=hexrgba('#ffffff'), anchor='mm')
    return glowify(c, col)
def ic_color():
    c, d = cv()
    for i in range(12):
        a = i / 12 * 2 * math.pi - math.pi / 2; r, g, b = colorsys.hsv_to_rgb(i / 12, 0.85, 1)
        x, y = 540 + 270 * math.cos(a), 560 + 270 * math.sin(a)
        d.ellipse((x - 62, y - 62, x + 62, y + 62), fill=(int(r * 255), int(g * 255), int(b * 255), 255))
    d.ellipse((440, 460, 640, 660), outline=hexrgba('#ffffff'), width=12)
    return glowify(c, '#ffffff', 26, 1.4)
def ic_cut():
    c, d = cv(); col = '#3fd8ff'; rnd = random.Random(3)
    for i in range(30):
        x = 140 + i * 27; gap = 12 <= i <= 17; h = 14 if gap else rnd.randint(60, 300)
        d.rounded_rectangle((x, 560 - h / 2, x + 14, 560 + h / 2), 7, fill=hexrgba('#ff4d4d' if gap else col))
    for x in (455, 630):
        for y in range(330, 800, 40): d.line((x, y, x, y + 22), fill=hexrgba('#ff4d4d'), width=8)
    d.ellipse((470, 820, 560, 910), outline=hexrgba('#ffffff'), width=12); d.ellipse((540, 820, 630, 910), outline=hexrgba('#ffffff'), width=12)
    d.line((530, 830, 640, 700), fill=hexrgba('#ffffff'), width=14); d.line((570, 830, 460, 700), fill=hexrgba('#ffffff'), width=14)
    return glowify(c, col)
def ic_clock():
    c, d = cv(); col = '#ffc21a'
    d.ellipse((260, 280, 820, 840), outline=hexrgba(col), width=LW)
    for i in range(12):
        a = i / 12 * 2 * math.pi; r1, r2 = (230, 262) if i % 3 else (205, 262)
        d.line((540 + r1 * math.sin(a), 560 - r1 * math.cos(a), 540 + r2 * math.sin(a), 560 - r2 * math.cos(a)), fill=hexrgba(col), width=10)
    d.ellipse((520, 540, 560, 580), fill=hexrgba('#ffffff')); d.rectangle((500, 220, 580, 270), fill=hexrgba(col))
    return glowify(c, col)
def ic_chart():
    c, d = cv(); col = '#5aff8a'
    for i, h in enumerate((180, 280, 240, 380, 520)):
        x = 270 + i * 120; d.rounded_rectangle((x, 860 - h, x + 80, 860), 12, outline=hexrgba(col), width=12)
    d.line((250, 640, 420, 520, 560, 580, 820, 300), fill=hexrgba('#ffffff'), width=14, joint='curve')
    d.polygon([(820, 300), (760, 300), (820, 360)], fill=hexrgba('#ffffff')); return glowify(c, col)
def ic_money():
    c, d = cv(); col = '#ffd400'
    for k, (x, y) in enumerate(((420, 640), (560, 560), (640, 700))):
        d.ellipse((x - 150, y - 150, x + 150, y + 150), fill=(20, 16, 4, 255), outline=hexrgba(col), width=LW)
        d.text((x, y), '$', font=ImageFont.truetype(FONTS['black'], 170), fill=hexrgba(col), anchor='mm')
    return glowify(c, col)
def ic_heart():
    c, d = cv(); col = '#ff2f8a'
    d.ellipse((300, 330, 560, 590), fill=hexrgba(col)); d.ellipse((520, 330, 780, 590), fill=hexrgba(col))
    d.polygon([(312, 500), (768, 500), (540, 840)], fill=hexrgba(col)); return glowify(c, col)
def ic_check():
    c, d = cv(); col = '#5aff8a'
    d.ellipse((290, 310, 790, 810), outline=hexrgba(col), width=LW)
    d.line((400, 570, 510, 680, 700, 450), fill=hexrgba('#ffffff'), width=30, joint='curve'); return glowify(c, col)
def ic_comment():
    c, d = cv(); col = '#3fd8ff'
    d.rounded_rectangle((230, 300, 850, 720), 60, outline=hexrgba(col), width=LW)
    d.polygon([(360, 710), (330, 860), (480, 712)], fill=hexrgba(col))
    for x in (400, 540, 680): d.ellipse((x - 34, 476, x + 34, 544), fill=hexrgba('#ffffff'))
    return glowify(c, col)
ICONS = dict(shop=(ic_shop, '#ff8a3d'), mic=(ic_mic, '#a07bff'), review=(ic_review, '#3fd8ff'), house=(ic_house, '#ffc21a'),
             car=(ic_car, '#ff4d4d'), phone=(ic_phone, '#ff2f8a'), ai=(ic_ai, '#3fd8ff'), color=(ic_color, '#ff6a3d'),
             cut=(ic_cut, '#3fd8ff'), clock=(ic_clock, '#ffc21a'), chart=(ic_chart, '#5aff8a'), money=(ic_money, '#ffd400'),
             heart=(ic_heart, '#ff2f8a'), check=(ic_check, '#5aff8a'), comment=(ic_comment, '#3fd8ff'))
_brc = {}
def broll_frame(kind, lt, dur, image=None):
    """kind: tên biểu tượng, hoặc 'image' với đường dẫn ảnh thật (Ken Burns)."""
    if kind == 'image':
        key = ('img', image)
        if key not in _brc:
            im = Image.open(image).convert('RGBA'); k = max(W / im.width, H / im.height) * 1.12
            _brc[key] = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        im = _brc[key]; z = 1 + 0.1 * (lt / max(dur, 0.1)); cw, ch = im.width / z, im.height / z
        x0 = (im.width - cw) / 2; y0 = (im.height - ch) / 2
        out = im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch))
        shade = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
        for y in range(H // 2, H, 8): sd.rectangle((0, y, W, y + 8), fill=(0, 0, 0, int(170 * (y - H / 2) / (H / 2))))
        out.alpha_composite(shade); return out
    if kind not in _brc:
        fn, col = ICONS[kind]; _brc[kind] = (br_background(col), fn(), col)
    bg, icon, col = _brc[kind]
    p = min(1, lt / 0.45); sc = 0.82 + 0.18 * ease_out(p) + 0.04 * (lt / max(dur, 0.1))
    bob = 0 if kind == 'car' else math.sin(lt * 3.2) * 10
    drift = int((1 - ease_out(p)) * -500) if kind == 'car' else 0
    out = bg.copy(); ic = icon.resize((int(S * sc), int(S * sc)), Image.BILINEAR)
    out.alpha_composite(ic, (int(ICX - ic.width / 2 + drift), int(ICY - ic.height / 2 + bob)))
    d = ImageDraw.Draw(out)
    if kind == 'clock':
        for sp, ln, w in ((6.0, 200, 12), (0.6, 140, 16)):
            a = lt * sp; cx, cy = ICX, ICY + 20 + bob
            d.line((cx, cy, cx + ln * math.sin(a), cy - ln * math.cos(a)), fill=hexrgba('#ffffff'), width=w)
    if kind in ('phone', 'heart'):
        for k in range(4):
            ph = (lt * 0.9 + k * 0.27) % 1; x = ICX + 210 + 40 * math.sin(k * 2 + lt * 4); y = ICY + 250 - ph * 520
            a = int(255 * math.sin(math.pi * ph)); r = 26
            d.ellipse((x - r, y - r, x, y), fill=hexrgba('#ff2f8a', a)); d.ellipse((x - 4, y - r, x + r - 4, y), fill=hexrgba('#ff2f8a', a))
            d.polygon([(x - r, y - r / 2 + 2), (x + r - 4, y - r / 2 + 2), (x - 2, y + r)], fill=hexrgba('#ff2f8a', a))
    rnd = random.Random(hash(kind) & 0xffff)
    for k in range(26):
        x0, y0, sp = rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(30, 90)
        y = (y0 - lt * sp) % H; r = rnd.choice((2, 3, 4))
        d.ellipse((x0 - r, y - r, x0 + r, y + r), fill=hexrgba(col, 150))
    return out

# ======================================================================
# prep / align / cuts
# ======================================================================
def cmd_prep(plan):
    inp = plan['input']
    run(['ffmpeg', '-v', 'error', '-y', '-i', inp, '-vn', '-ac', '1', '-ar', str(SR), wp(plan, 'voice.wav')])
    # giữ khung dọc 9:16: scale + crop vào giữa nếu tỉ lệ khác
    vf = f'scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}'
    run(['ffmpeg', '-v', 'error', '-y', '-i', inp, '-vf', vf, '-r', str(FPS), '-an', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '14', wp(plan, 'base.mp4')])
    print('prep xong:', wp(plan, 'base.mp4'))

def envelope(plan, hop_s=0.02):
    from scipy.io import wavfile
    from scipy.signal import butter, sosfilt
    sr, a = wavfile.read(wp(plan, 'voice.wav')); a = a.astype(np.float32) / 32768
    a = sosfilt(butter(2, [120, 4000], 'band', fs=sr, output='sos'), a)
    hop = int(sr * hop_s); n = len(a) // hop
    db = 20 * np.log10(np.sqrt(np.mean(a[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
    floor = np.percentile(db, 10)
    thr = plan.get('silence_db', max(floor + 7, -45))
    return db, thr, hop_s

def pauses_from(db, thr, hop_s, min_len):
    v = db > thr; out = []; i = 0; n = len(v)
    while i < n:
        if not v[i]:
            j = i
            while j < n and not v[j]: j += 1
            if (j - i) * hop_s >= min_len: out.append((i * hop_s, j * hop_s))
            i = j
        else: i += 1
    return out, n * hop_s

EN2 = {'podcast', 'review', 'tiktok', 'youtube', 'short', 'reel', 'skill', 'comment', 'video', 'edit', 'zoom', 'online', 'livestream', 'marketing', 'content', 'follow', 'like', 'share', 'website', 'app'}
def syl(line):
    return sum(2 if w.lower().strip('.,?!"\'') in EN2 else 1 for w in line.replace("'", ' ').split())

def cmd_align(plan):
    """Khớp câu vào các quãng ngắt bằng quy hoạch động: thời lượng nói của mỗi câu
    tỉ lệ với số âm tiết, ưu tiên ranh giới ở các quãng ngắt dài."""
    lines = plan['lines']
    db, thr, hop = envelope(plan, 0.05)
    v = db > thr
    pauses, total = pauses_from(db, thr, hop, 0.15)
    first = next(i for i, x in enumerate(v) if x) * hop
    last = (len(v) - next(i for i, x in enumerate(v[::-1]) if x)) * hop
    pauses = [p for p in pauses if p[0] > first + 0.1 and p[1] < last - 0.1]
    vt = np.concatenate([[0], np.cumsum(v)]) * hop
    def voiced(a, b): return vt[min(len(vt) - 1, int(round(b / hop)))] - vt[min(len(vt) - 1, int(round(a / hop)))]
    ns = [syl(l) for l in lines]; L = len(lines)
    r = voiced(first, last) / sum(ns)
    # điểm mốc: 0 = đầu, 1..P = các quãng ngắt, P+1 = cuối
    pts = [(first, first)] + pauses + [(last, last)]; P = len(pts)
    INF = 1e18
    cost = [[INF] * P for _ in range(L + 1)]; back = [[-1] * P for _ in range(L + 1)]
    cost[0][0] = 0
    for k in range(1, L + 1):
        exp = ns[k - 1] * r
        for j in range(1, P):
            if k == L and j != P - 1: continue
            if k < L and j == P - 1: continue
            bonus = -0.6 * min(0.8, pts[j][1] - pts[j][0]) if k < L else 0
            for i in range(0, j):
                if cost[k - 1][i] >= INF: continue
                d = voiced(pts[i][1], pts[j][0])
                c = cost[k - 1][i] + (d - exp) ** 2 / (exp + 0.4) + bonus
                if c < cost[k][j]: cost[k][j] = c; back[k][j] = i
    idx = [P - 1]
    for k in range(L, 0, -1): idx.append(back[k][idx[-1]])
    idx = idx[::-1]
    out = []
    for k in range(L):
        s, e = pts[idx[k]][1], pts[idx[k + 1]][0]
        out.append(dict(i=k, text=lines[k], start=round(s, 2), end=round(max(e, s + 0.3), 2)))
    for k, (s, e) in (plan.get('line_times') or {}).items():
        out[int(k)]['start'], out[int(k)]['end'] = s, e
    json.dump(out, open(wp(plan, 'lines.json'), 'w'), ensure_ascii=False, indent=1)
    for o in out: print(f"{o['i']:2d} {o['start']:6.2f}-{o['end']:6.2f}  {o['text'][:70]}")

def cmd_cuts(plan):
    db, thr, hop = envelope(plan, 0.02)
    if not plan.get('cut_silence', True):
        total = len(db) * hop; keep = [(0.0, total)]
    else:
        min_gap = plan.get('min_pause', 0.24); pad_in, pad_out = 0.07, 0.10
        pauses, total = pauses_from(db, thr, hop, 0.02)
        keep = []; cur = 0.0
        for s, e in pauses:
            if s == 0.0: cur = max(0.0, e - 0.12); continue
            if e >= total - 0.05:
                if s + pad_out > cur: keep.append((cur, s + pad_out))
                cur = total; break
            if e - s >= min_gap:
                if s + pad_out > cur: keep.append((cur, s + pad_out))
                cur = e - pad_in
        if cur < total - 0.05: keep.append((cur, total))
        # cắt thủ công thêm (đoạn thừa) theo thời gian gốc
        for cs, ce in plan.get('extra_cuts', []):
            nk = []
            for s, e in keep:
                if ce <= s or cs >= e: nk.append((s, e)); continue
                if s < cs: nk.append((s, cs))
                if ce < e: nk.append((ce, e))
            keep = nk
    keep = [(round(s * FPS) / FPS, round(e * FPS) / FPS) for s, e in keep]
    keep = [(s, e) for s, e in keep if e - s > 0.05]
    json.dump(keep, open(wp(plan, 'keep.json'), 'w'))
    newdur = sum(e - s for s, e in keep)
    print(f'{len(keep)} đoạn giữ lại; {total:.2f}s -> {newdur:.2f}s')

def mapper(keep):
    starts = []; acc = 0.0
    for s, e in keep: starts.append(acc); acc += e - s
    def f(t):
        for (s, e), ns in zip(keep, starts):
            if t < s: return ns
            if t <= e: return ns + (t - s)
        return acc
    return f, acc

# ======================================================================
# Lập lịch tiêu đề / ảnh trám theo thời gian
# ======================================================================
def resolve(plan):
    lines = json.load(open(wp(plan, 'lines.json')))
    def span(item):
        if 'start' in item: return item['start'], item['end']
        a = lines[item['line']]; s, e = a['start'], a['end']
        if 'line_to' in item: e = lines[item['line_to']]['end']
        if 'part' in item:
            p0, p1 = item['part']; s, e = s + (e - s) * p0, s + (e - s) * p1
        return s, e
    cy0 = int(plan.get('title_y', 0.8) * H)
    T = []
    for it in plan.get('titles', []):
        s, e = span(it)
        T.append(dict(start=s - 0.05, dur=max(0.5, e - s + 0.25), cx=W // 2 + it.get('dx', 0),
                      cy=int(it['y'] * H) if 'y' in it else cy0, anim=it.get('anim', 'blur'),
                      layers=[make_layer(L) for L in it['layers']]))
    # kéo dài để tiêu đề nối nhau (không bị trống giữa 2 câu)
    T.sort(key=lambda x: x['start'])
    for a, b in zip(T, T[1:]):
        if 0 < b['start'] - (a['start'] + a['dur']) < 0.6: a['dur'] = b['start'] - a['start'] - 0.02
        if a['start'] + a['dur'] > b['start']: a['dur'] = max(0.4, b['start'] - a['start'] - 0.02)
    B = []
    for it in plan.get('broll', []):
        s, e = span(it); B.append((s, e, it.get('kind', 'image'), it.get('image')))
    P = [span(it) for it in plan.get('punch', [])]
    return T, B, P

# ======================================================================
# Âm thanh
# ======================================================================
def build_audio(plan, T, B, P, f, newdur):
    from scipy.io import wavfile
    from scipy.signal import butter, sosfilt
    rng = np.random.default_rng(7)
    lp = lambda x, fc, o=2: sosfilt(butter(o, fc, 'low', fs=SR, output='sos'), x)
    hp = lambda x, fc, o=2: sosfilt(butter(o, fc, 'high', fs=SR, output='sos'), x)
    bp = lambda x, lo, hi: sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)
    keep = json.load(open(wp(plan, 'keep.json')))
    sr, v = wavfile.read(wp(plan, 'voice.wav')); v = v.astype(np.float32) / 32768
    FADE = int(0.008 * SR); parts = []
    for s, e in keep:
        seg = v[int(s * SR):int(e * SR)].copy(); r = np.linspace(0, 1, min(FADE, len(seg) // 2) or 1)
        seg[:len(r)] *= r; seg[len(seg) - len(r):] *= r[::-1]; parts.append(seg)
    voice = hp(np.concatenate(parts), 80)
    voice *= 0.5 / (np.percentile(np.abs(voice), 99.5) + 1e-9)
    N = len(voice) + int(0.6 * SR); voice = np.pad(voice, (0, N - len(voice))); t = np.arange(N) / SR

    def place(buf, sig, at):
        i = int(at * SR)
        if i >= len(buf) or i + len(sig) <= 0: return
        j = min(len(buf), i + len(sig)); buf[max(i, 0):j] += sig[max(0, -i):j - i]
    music = np.zeros(N)
    if plan.get('music_file'):
        tmp = wp(plan, 'music_in.wav')
        run(['ffmpeg', '-v', 'error', '-y', '-stream_loop', '-1', '-i', plan['music_file'], '-t', str(N / SR), '-ac', '1', '-ar', str(SR), tmp])
        _, m = wavfile.read(tmp); m = m.astype(np.float32) / 32768
        m = np.pad(m, (0, max(0, N - len(m))))[:N]; music = m * (0.25 / (np.sqrt(np.mean(m ** 2)) + 1e-9)) * 0.55
    elif plan.get('music', True):
        BPM = plan.get('bpm', 110); beat = 60 / BPM; bar = 4 * beat
        midi = lambda m: 440 * 2 ** ((m - 69) / 12)
        CH = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]; RT = [45, 41, 48, 43]
        def env_ad(n, a, d):
            e = np.ones(n); na = max(1, int(a * SR)); e[:na] = np.linspace(0, 1, na); e[na:] = np.exp(-np.arange(n - na) / (d * SR)); return e
        pad = np.zeros(N)
        for b in range(int(np.ceil(N / SR / bar)) + 1):
            n = int(bar * SR); tt = np.arange(n) / SR; sig = np.zeros(n)
            for m in CH[b % 4]:
                for det in (-0.12, 0.0, 0.11): sig += 2 * ((tt * midi(m + 12) * 2 ** (det / 12)) % 1) - 1
            place(pad, sig * np.minimum(1, tt / 0.25) * np.minimum(1, (bar - tt) / 0.15) * 0.025, b * bar)
        pad = lp(pad, 1500, 4); pump = np.ones(N)
        for k in range(int(N / SR / beat) + 1):
            i = int(k * beat * SR); n = int(beat * SR); seg = 1 - 0.55 * np.exp(-np.arange(n) / (0.09 * SR))
            pump[i:i + n] = seg[:max(0, min(n, N - i))]
        music += pad * pump
        for k in range(int(N / SR / (beat / 2)) + 1):
            st = k * beat / 2; b = int(st / bar); fr = midi(RT[b % 4] - 12 + (12 if k % 4 == 3 else 0))
            n = int(beat / 2 * SR * 0.9); tt = np.arange(n) / SR
            place(music, np.tanh(2.2 * np.sin(2 * np.pi * fr * tt)) * env_ad(n, 0.005, 0.12) * 0.16, st)
        kt = np.arange(int(0.35 * SR)) / SR
        kick = np.sin(2 * np.pi * (50 * kt + 90 * (1 - np.exp(-kt / 0.03)) * 0.03)) * np.exp(-kt / 0.12) * 0.55
        cn = int(0.2 * SR); clap = bp(rng.standard_normal(cn), 900, 3500) * np.exp(-np.arange(cn) / (0.05 * SR)) * 0.22
        hn = int(0.05 * SR); hat = hp(rng.standard_normal(hn), 7000) * np.exp(-np.arange(hn) / (0.012 * SR)) * 0.09
        INTRO = 2 * bar
        for k in range(int(N / SR / beat) + 1):
            st = k * beat
            if st >= INTRO or k % 4 == 0: place(music, kick, st)
            if k % 4 in (1, 3) and st >= INTRO: place(music, clap, st)
            place(music, hat * (0.6 if st < INTRO else 1), st + beat / 2)
            if st >= INTRO: place(music, hat * 0.5, st + beat / 4); place(music, hat * 0.5, st + 3 * beat / 4)
        for k in range(int(N / SR / (beat / 4)) + 1):
            st = k * beat / 4; b = int(st / bar)
            if st < INTRO: continue
            ch = CH[b % 4]; m = ch[k % 3] + 24 if k % 2 == 0 else ch[(k + 1) % 3] + 12
            n = int(0.18 * SR); tt = np.arange(n) / SR
            place(music, (2 * np.abs(2 * ((tt * midi(m)) % 1) - 1) - 1) * env_ad(n, 0.002, 0.06) * 0.035, st)
        music = lp(music, 9000)
    music *= np.minimum(1, t / 1.0) * np.minimum(1, (t[-1] - t) / 1.5)
    # ducking
    hop = 480; ve = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, 'same')); active = (ve > 0.02).astype(float)
    g = np.zeros(N); cur = 0.0; step = 48
    a_c, r_c = 1 - np.exp(-1 / (0.03 * SR)), 1 - np.exp(-1 / (0.35 * SR))
    for i in range(0, N, step):
        c = a_c if active[i] > cur else r_c; cur += (active[i] - cur) * (1 - (1 - c) ** step); g[i:i + step] = cur
    mv = plan.get('music_volume', 1.0)
    music_gain = (0.9 - 0.6 * g) * mv
    # SFX
    sfx = np.zeros(N)
    def whoosh(d=0.34, up=True, amp=0.16):
        n = int(d * SR); tt = np.arange(n) / SR; noise = rng.standard_normal(n); out = np.zeros(n)
        for k in range(24):
            a, b = k * n // 24, (k + 1) * n // 24; fc = 300 + (4500 if up else 2500) * (k / 24 if up else 1 - k / 24)
            out[a:b] = bp(noise, fc * 0.6, min(fc * 1.6, 20000))[a:b]
        return out * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.6 * amp
    def pop(amp=0.32):
        n = int(0.09 * SR); tt = np.arange(n) / SR; fr = 900 * np.exp(-tt / 0.03) + 180
        return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / 0.03) * amp
    def ding(amp=0.16):
        n = int(0.9 * SR); tt = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318 * tt) + 0.5 * np.sin(2 * np.pi * 1975 * tt) + 0.25 * np.sin(2 * np.pi * 2637 * tt)) * np.exp(-tt / 0.25) * amp
    def riser(d=0.8, amp=0.2):
        n = int(d * SR); tt = np.arange(n) / SR; fr = 200 + 1600 * (tt / d) ** 2
        return (hp(rng.standard_normal(n), 2000) * 0.5 + np.sin(2 * np.pi * np.cumsum(fr) / SR) * 0.4) * (tt / d) ** 2 * amp
    def impact(amp=0.45):
        n = int(0.8 * SR); tt = np.arange(n) / SR; fr = 120 * np.exp(-tt / 0.15) + 40
        return (np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-tt / 0.3) + lp(rng.standard_normal(n), 800) * np.exp(-tt / 0.08) * 0.5) * amp
    if plan.get('sfx', True):
        for k, ti in enumerate(T):
            if ti['anim'] == 'pop': place(sfx, pop(), ti['start'] + 0.02)
            elif ti['anim'] != 'spread': place(sfx, whoosh(0.34, k % 2 == 0), ti['start'] - 0.12)
        for s, e, kind, img in B: place(sfx, whoosh(0.22, True, 0.18), s - 0.08)
        for s, e in P: place(sfx, impact(0.35), s)
        for ev in plan.get('sfx_events', []):   # [{"at_line": i, "type": "riser|impact|ding", "offset": 0}]
            lines = json.load(open(wp(plan, 'lines.json')))
            at = f(lines[ev['at_line']]['start']) + ev.get('offset', 0)
            sig = {'riser': lambda: riser(), 'impact': lambda: impact(), 'ding': lambda: ding(), 'pop': lambda: pop(), 'whoosh': lambda: whoosh()}[ev['type']]()
            place(sfx, sig, at - (0.75 if ev['type'] == 'riser' else 0))
    mix = voice + music * music_gain * 0.5 + sfx * plan.get('sfx_volume', 1.0)
    mix = np.tanh(mix * 1.1) / np.tanh(1.1); mix *= 0.89 / np.max(np.abs(mix))
    wavfile.write(wp(plan, 'mix.wav'), SR, (mix * 32767).astype(np.int16))

# ======================================================================
# Hình
# ======================================================================
def to_new_time(T, B, P, f):
    for ti in T:
        s, e = f(ti['start']), f(ti['start'] + ti['dur']); ti['start'], ti['dur'] = s, max(0.4, e - s)
    B = [(f(s), f(e), k, im) for s, e, k, im in B]
    B = [(s, (B[j + 1][0] if j + 1 < len(B) and B[j + 1][0] - e < 0.15 else e), k, im) for j, (s, e, k, im) in enumerate(B)]
    P = [(f(s), f(e)) for s, e in P]
    return T, B, P

def frames(plan, T, B, P, newdur, only=None):
    keep = json.load(open(wp(plan, 'keep.json')))
    starts = sorted(ti['start'] for ti in T)
    ZOOMS = plan.get('zoom_levels', [1.0, 1.14, 1.06, 1.2]) if plan.get('zoom', True) else [1.0]
    FCX, FCY = plan.get('face', [0.5, 0.33])
    def zoom_at(nt):
        z = ZOOMS[sum(1 for s in starts if s <= nt + 1e-6) % len(ZOOMS)]
        for s, e in P:
            if s - 0.05 <= nt <= e + 0.1: z = 1.0 + 0.42 * ease_out(min(1, (nt - s + 0.05) / 0.12))
        return z
    def apply_zoom(img, z):
        if z <= 1.001: return img
        cw, ch = W / z, H / z
        x0 = min(max(FCX * W - cw / 2, 0), W - cw); y0 = min(max(FCY * H - ch / 2, 0), H - ch)
        return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    src = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', wp(plan, 'base.mp4'), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    fsz = W * H * 3; i = 0; nout = 0; ki = 0
    while True:
        buf = src.stdout.read(fsz)
        if len(buf) < fsz: break
        t = i / FPS; i += 1
        while ki < len(keep) and t >= keep[ki][1]: ki += 1
        if ki >= len(keep): break
        if t < keep[ki][0]: continue
        nt = nout / FPS; nout += 1
        if only is not None and not any(abs(nt - o) < 0.5 / FPS for o in only): continue
        img = apply_zoom(Image.frombuffer('RGB', (W, H), buf, 'raw', 'RGB', 0, 1), zoom_at(nt)).convert('RGBA')
        for j, (s, e, k, im) in enumerate(B):
            if s <= nt < e:
                bimg = broll_frame(k, nt - s, e - s, im)
                pa = j > 0 and s - B[j - 1][1] < 0.15; na = j + 1 < len(B) and B[j + 1][0] - e < 0.15
                a = min(1.0 if pa else min(1, (nt - s) / 0.12), 1.0 if na else min(1, (e - nt) / 0.12))
                img = bimg.copy() if a >= 0.999 else Image.blend(img, bimg, a)
        draw_titles(T, nt, img)
        yield nt, img
    src.kill()

def cmd_preview(plan):
    T, B, P = resolve(plan)
    n = len(T) + len(B); cols = min(10, n); rows = math.ceil(n / cols)
    sheet = Image.new('RGB', (216 * cols, 384 * rows))
    bg = Image.open(wp(plan, 'preview_bg.png')).convert('RGBA') if os.path.exists(wp(plan, 'preview_bg.png')) else None
    if bg is None:
        run(['ffmpeg', '-v', 'error', '-y', '-ss', '2', '-i', wp(plan, 'base.mp4'), '-frames:v', '1', wp(plan, 'preview_bg.png')])
        bg = Image.open(wp(plan, 'preview_bg.png')).convert('RGBA')
    k = 0
    for ti in T:
        c = bg.copy(); draw_titles(T, ti['start'] + min(1.2, ti['dur'] - 0.36), c)
        sheet.paste(c.convert('RGB').resize((216, 384)), ((k % cols) * 216, (k // cols) * 384)); k += 1
    for s, e, kind, im in B:
        c = broll_frame(kind, 0.8, e - s, im)
        sheet.paste(c.convert('RGB').resize((216, 384)), ((k % cols) * 216, (k // cols) * 384)); k += 1
    sheet.save(wp(plan, 'preview.jpg'), quality=85); print('đã lưu', wp(plan, 'preview.jpg'))

def cmd_render(plan):
    keep = json.load(open(wp(plan, 'keep.json'))); f, newdur = mapper(keep)
    T, B, P = resolve(plan); T, B, P = to_new_time(T, B, P, f)
    build_audio(plan, T, B, P, f, newdur)
    master = wp(plan, 'master.mp4')
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', wp(plan, 'mix.wav'), '-map', '0:v', '-map', '1:a', '-vf', plan.get('grade', 'eq=contrast=1.05:saturation=1.12'),
                            '-c:v', 'libx264', '-preset', 'fast', '-crf', '17', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', master],
                           stdin=subprocess.PIPE)
    n = 0
    for nt, img in frames(plan, T, B, P, newdur):
        enc.stdin.write(img.convert('RGB').tobytes()); n += 1
        if n % 150 == 0: print(f'  {nt:.1f}s / {newdur:.1f}s', flush=True)
    enc.stdin.close(); enc.wait()
    out = plan['output']; max_mb = plan.get('max_mb', 29)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', master], capture_output=True, text=True).stdout)
    if os.path.getsize(master) / 1e6 <= max_mb:
        run(['ffmpeg', '-v', 'error', '-y', '-i', master, '-c', 'copy', '-movflags', '+faststart', out])
    else:
        vb = int(max(800, (max_mb * 8e6 * 0.95 / dur - 160e3) / 1000))
        pl = wp(plan, 'pass')
        run(['ffmpeg', '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{vb}k', '-pass', '1', '-passlogfile', pl, '-an', '-f', 'mp4', '/dev/null'])
        run(['ffmpeg', '-v', 'error', '-y', '-i', master, '-c:v', 'libx264', '-preset', 'medium', '-b:v', f'{vb}k', '-pass', '2', '-passlogfile', pl,
             '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out])
    print(f'XONG: {out} ({os.path.getsize(out) / 1e6:.1f} MB, {dur:.1f}s)')

def cmd_probe(plan, times):
    keep = json.load(open(wp(plan, 'keep.json'))); f, newdur = mapper(keep)
    T, B, P = resolve(plan); T, B, P = to_new_time(T, B, P, f)
    imgs = [img.convert('RGB').resize((240, 427)) for nt, img in frames(plan, T, B, P, newdur, only=times)]
    sheet = Image.new('RGB', (240 * len(imgs), 427))
    for k, im in enumerate(imgs): sheet.paste(im, (k * 240, 0))
    sheet.save(wp(plan, 'probe.jpg'), quality=85); print('đã lưu', wp(plan, 'probe.jpg'))

if __name__ == '__main__':
    cmd, plan_path = sys.argv[1], sys.argv[2]
    plan = load(plan_path)
    {'prep': cmd_prep, 'align': cmd_align, 'cuts': cmd_cuts, 'preview': cmd_preview, 'render': cmd_render}.get(cmd, lambda p: None)(plan)
    if cmd == 'probe': cmd_probe(plan, [float(x) for x in sys.argv[3:]])
