"""Render a talking-head video with TikTok-style real-estate graphics from a plan.json.

Usage: python3 render.py <plan.json> <output.mp4>

See ../SKILL.md for the plan format and ../examples/plan-example.json for a full example.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import ffmpeg_exe, media_info  # noqa: E402

FD = os.path.join(HERE, "..", "assets", "fonts")
COLORS = {"white": (255, 255, 255), "yellow": (255, 216, 74), "cyan": (64, 236, 255), "red": (214, 40, 40),
          "teal": (0, 170, 170), "green": (46, 196, 90), "black": (0, 0, 0), "navy": (10, 24, 66)}


def color(c, default="white"):
    c = c or default
    if isinstance(c, (list, tuple)):
        return tuple(c)
    if c.startswith("#"):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    return COLORS[c]


_fonts = {}


def font(kind, size):
    key = (kind, size)
    if key not in _fonts:
        if kind == "heading":
            f = ImageFont.truetype(f"{FD}/Oswald[wght].ttf", size); f.set_variation_by_name("Bold")
        elif kind == "script":
            f = ImageFont.truetype(f"{FD}/DancingScript[wght].ttf", size); f.set_variation_by_name("Bold")
        else:
            f = ImageFont.truetype(f"{FD}/BeVietnamPro-ExtraBold.ttf", size)
        _fonts[key] = f
    return _fonts[key]


# ---------- easing / compositing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): return 1 - (1 - clamp(x)) ** 3


def back_out(x):
    x = clamp(x); c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def with_alpha(layer, a):
    if a >= 1: return layer
    layer = layer.copy(); layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return layer


def place(canvas, layer, cx, cy, scale=1.0, alpha=1.0, blur=0.0):
    if alpha <= 0.01 or scale <= 0: return
    if abs(scale - 1) > 0.005:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.LANCZOS)
    if blur > 0.3:
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
    canvas.alpha_composite(with_alpha(layer, alpha), (int(cx - layer.width / 2), int(cy - layer.height / 2)))


def drop_shadow(size, box, radius, blur=12, offset=8, alpha=150):
    sh = Image.new("RGBA", size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + offset, x1, y1 + offset), radius, fill=(0, 0, 0, alpha))
    return sh.filter(ImageFilter.GaussianBlur(blur))


def text_layer(txt, f, fill, stroke=6, shadow=True):
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    pad = 30
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 6), txt, font=f, fill=(0, 0, 0, 160),
                                stroke_width=stroke, stroke_fill=(0, 0, 0, 160))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=(0, 0, 0))
    return im


def grid_background(W, H):
    top, bot = np.array([0, 0, 0]), np.array([16, 40, 150])
    k = np.clip((np.linspace(0, 1, H) - 0.35) / 0.65, 0, 1) ** 1.4
    grad = (top + (bot - top) * k[:, None]).astype(np.uint8)
    im = Image.fromarray(np.repeat(grad[:, None, :], W, axis=1))
    d = ImageDraw.Draw(im, "RGBA")
    step = W // 9
    for x in range(0, W + 1, step): d.line((x, 0, x, H), fill=(255, 255, 255, 60), width=2)
    for y in range(0, H + 1, step): d.line((0, y, W, y), fill=(255, 255, 255, 60), width=2)
    return im


# ---------- element builders (each returns an RGBA layer) ----------
def build_card(e):
    w, h, r = 900, 330, 34
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im = Image.alpha_composite(im, drop_shadow(im.size, (20, 20, w + 20, h + 20), r))
    top, bot = np.array([10, 24, 66]), np.array([28, 78, 186])
    grad = (top + (bot - top) * np.linspace(0, 1, h)[:, None]).astype(np.uint8)
    body = Image.fromarray(np.repeat(grad[:, None, :], w, axis=1)).convert("RGBA")
    d = ImageDraw.Draw(body)
    for x in range(0, w, 60): d.line((x, 0, x, h), fill=(255, 255, 255, 28), width=2)
    for y in range(0, h, 60): d.line((0, y, w, y), fill=(255, 255, 255, 28), width=2)
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    im.paste(body, (20, 20), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 19, h + 19), r, outline=color(e.get("border"), "red"), width=7)
    small = e.get("small", "")
    if small:
        d.text((20 + w / 2, 82), "  ".join(small.upper()).replace("     ", "   "), font=font("heading", 50),
               fill=(230, 236, 255), anchor="mm")
    big = e.get("big", "")
    fb = font("heading", 150)
    while fb.size > 60 and d.textlength(big, font=fb) > w - 60:
        fb = font("heading", fb.size - 10)
    d.text((20 + w / 2, 192 if small else 160), big, font=fb, fill=(255, 255, 255), anchor="mm",
           stroke_width=3, stroke_fill=(0, 0, 0))
    loc = e.get("location")
    if loc:
        f3 = font("body", 46); tw = d.textlength(loc, font=f3)
        px, py = 20 + w / 2 - tw / 2 - 26, 298
        red = color("red")
        d.ellipse((px - 18, py - 30, px + 18, py + 6), fill=red)
        d.polygon([(px - 15, py - 6), (px + 15, py - 6), (px, py + 22)], fill=red)
        d.ellipse((px - 7, py - 19, px + 7, py - 5), fill=(255, 255, 255))
        d.text((px + 30, py - 4), loc, font=f3, fill=color("yellow"), anchor="lm")
    return im


def draw_icon(d, kind, cx, cy, R, fg):
    if kind == "clock":
        d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=fg, width=9)
        d.line((cx, cy, cx, cy - R * 0.6), fill=fg, width=9); d.line((cx, cy, cx + R * 0.48, cy + R * 0.23), fill=fg, width=9)
    elif kind == "check":
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=color("green"))
        d.line([(cx - R * 0.45, cy), (cx - R * 0.1, cy + R * 0.38), (cx + R * 0.5, cy - R * 0.35)], fill=(255, 255, 255),
               width=max(4, int(R * 0.22)), joint="curve")


def build_badge(e):
    f = font("heading", e.get("size", 96)); txt = e["text"]
    icon = e.get("icon", "none")
    tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(txt, font=f))
    h = int(f.size * 1.56); lead = int(h * 1.07) if icon != "none" else h // 2
    w = tw + lead + h // 2
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im = Image.alpha_composite(im, drop_shadow(im.size, (20, 20, w + 20, h + 20), h // 2, blur=10))
    d = ImageDraw.Draw(im)
    bg, fg = color(e.get("color"), "yellow"), color(e.get("text_color"), "black")
    d.rounded_rectangle((20, 20, w + 20, h + 20), h // 2, fill=bg, outline=(0, 0, 0), width=5)
    if icon != "none":
        draw_icon(d, icon, 20 + h * 0.61, 20 + h / 2, h * 0.29, fg)
    d.text((20 + lead, 20 + h / 2 + 2), txt, font=f, fill=fg, anchor="lm")
    return im


def build_chip(text, size=52):
    """Grey pill with green check, like the sample's 'Thanh toán sớm' chips."""
    f = font("heading", size)
    tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(text.upper(), font=f))
    h = int(size * 1.5); w = tw + h + 40
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im = Image.alpha_composite(im, drop_shadow(im.size, (20 + h, 20, w + 20, h + 20), 14, blur=8, offset=5))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20 + h - 10, 24, w + 20, h + 16), 14, fill=(120, 120, 128, 235), outline=(255, 255, 255), width=3)
    draw_icon(d, "check", 20 + h * 0.42, 20 + h / 2, h * 0.36, None)
    d.text((20 + h + 15, 20 + h / 2), text.upper(), font=f, fill=(255, 255, 255), anchor="lm")
    return im


def build_image(e, plan_dir):
    path = e["path"] if os.path.isabs(e["path"]) else os.path.join(plan_dir, e["path"])
    src = Image.open(path).convert("RGB")
    w = e.get("width", 860); h = e.get("height") or int(w * src.height / src.width)
    # cover-crop into w x h
    s = max(w / src.width, h / src.height)
    src = src.resize((int(src.width * s) + 1, int(src.height * s) + 1), Image.LANCZOS)
    src = src.crop(((src.width - w) // 2, (src.height - h) // 2, (src.width - w) // 2 + w, (src.height - h) // 2 + h))
    r = 26
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    im = Image.alpha_composite(im, drop_shadow(im.size, (20, 20, w + 20, h + 20), r))
    mask = Image.new("L", (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    im.paste(src, (20, 20), mask)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, w + 19, h + 19), r, outline=color(e.get("border"), "red"), width=6)
    if e.get("label"):
        lab = text_layer(e["label"], font("heading", e.get("label_size", 96)), color(e.get("label_color"), "white"), 6)
        im.alpha_composite(lab, ((im.width - lab.width) // 2, im.height - 20 - int(lab.height * 0.78)))
    return im


def build_arrow(e):
    L = e.get("length", 120); c = color(e.get("color"), "red")
    im = Image.new("RGBA", (80, L + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line((40, 0, 40, L - 30), fill=c, width=12)
    d.polygon([(10, L - 40), (70, L - 40), (40, L + 10)], fill=c)
    return im


# ---------- renderer ----------
class Renderer:
    def __init__(self, plan, plan_dir):
        self.p = plan; self.dir = plan_dir
        o = plan.get("output", {})
        self.W, self.H, self.fps = o.get("width", 1080), o.get("height", 1920), o.get("fps", 30)
        self.cache = {}
        self.grid = grid_background(self.W, self.H) if plan.get("grid") else None
        cs = plan.get("caption_style", {})
        self.cap_y, self.cap_size = cs.get("y", int(self.H * 0.69)), cs.get("size", 62)
        self.cap_hl = color(cs.get("highlight"), "yellow")
        self.cap_font = font("body", self.cap_size)

    def layer(self, i, e):
        if i in self.cache: return self.cache[i]
        t = e["type"]
        if t == "text":
            L = text_layer(e["text"], font(e.get("font", "heading"), e.get("size", 96)), color(e.get("color")), e.get("stroke", 6))
        elif t == "card": L = build_card(e)
        elif t == "badge": L = build_badge(e)
        elif t == "image": L = build_image(e, self.dir)
        elif t == "arrow": L = build_arrow(e)
        else: L = None
        if L is not None and e.get("scale", 1) != 1:
            s = e["scale"]; L = L.resize((int(L.width * s), int(L.height * s)), Image.LANCZOS)
        self.cache[i] = L
        return L

    def animate(self, c, L, e, t, out):
        x, y = e.get("x", self.W / 2), e.get("y", self.H / 2)
        k = (t - e["start"]) / e.get("anim_dur", 0.28)
        anim = e.get("anim", "pop")
        if anim == "pop":
            place(c, L, x, y, scale=0.55 + 0.45 * back_out(k), alpha=ease_out(k * 1.6) * out)
        elif anim == "blur":
            a = ease_out(k); place(c, L, x, y, alpha=a * out, blur=14 * (1 - a))
        elif anim == "slide":
            a = ease_out(k); place(c, L, x, y + 60 * (1 - a), alpha=a * out)
        else:
            place(c, L, x, y, alpha=out)

    def element(self, c, i, e, t):
        end = e.get("end", 1e9)
        if t < e["start"] or t >= end + 0.15: return
        out = 1 - clamp((t - end) / 0.15)
        typ = e["type"]
        if typ == "title":
            self.title(c, i, e, t, out)
        elif typ == "counter":
            k = ease_out((t - e["start"]) / e.get("duration", 0.75))
            v = e.get("from", 0) + (e["to"] - e.get("from", 0)) * k
            dec = e.get("decimals", 0)
            s = f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")  # Vietnamese separators
            L = text_layer(e.get("prefix", "") + s + e.get("suffix", ""), font(e.get("font", "script"), e.get("size", 330)),
                           color(e.get("color"), "cyan"), 8)
            a = ease_out((t - e["start"]) / 0.25)
            place(c, L, e.get("x", self.W / 2), e.get("y", self.H / 2), scale=0.8 + 0.2 * a, alpha=a * out)
        elif typ == "checklist":
            x0, y0, gap = e.get("x", 60), e.get("y", 300), e.get("gap", 110)
            for j, it in enumerate(e["items"]):
                if t < it["at"]: continue
                key = (i, j)
                if key not in self.cache: self.cache[key] = build_chip(it["text"], e.get("size", 52))
                L = self.cache[key]
                k = (t - it["at"]) / 0.26
                place(c, L, x0 + L.width / 2, y0 + j * gap, scale=0.6 + 0.4 * back_out(k), alpha=ease_out(k * 1.6) * out)
        else:
            self.animate(c, self.layer(i, e), e, t, out)

    def title(self, c, i, e, t, out):
        y = e.get("y", int(self.H * 0.122)); size = e.get("size", 118)
        key = (i, "t")
        if key not in self.cache:
            self.cache[key] = (text_layer(e["line1"], font("heading", size), color(e.get("color1"), "white"), 7),
                               text_layer(e["line2"], font("heading", size), color(e.get("color2"), "yellow"), 7)
                               if e.get("line2") else None)
        L1, L2 = self.cache[key]
        y2 = y + int(size * 1.62)
        t2 = e.get("line2_at", e["start"] + 0.6)
        if L2 is not None and t >= t2:  # bar wipes in first, then line 2 reveals on top of it
            k = ease_out((t - t2) / 0.2)
            bw, bh = L2.width - 20, L2.height - 40
            bar = Image.new("RGBA", (max(1, int(bw * k)), bh), color(e.get("bar"), "teal") + (int(235 * out),))
            c.alpha_composite(bar, (int(self.W / 2 - bw / 2), int(y2 - bh / 2)))
            if t >= t2 + 0.14:
                place(c, L2, self.W / 2, y2, alpha=ease_out((t - t2 - 0.14) / 0.12) * out)
        k = (t - e["start"]) / 0.28  # line 1 drawn last so the bar never hides its diacritics
        place(c, L1, self.W / 2, y, scale=0.55 + 0.45 * back_out(k), alpha=ease_out(k * 1.6) * out)

    def caption(self, c, t):
        for cap in self.p.get("captions", []):
            s, e, words = cap["start"], cap["end"], cap["words"]
            if not (s <= t < e): continue
            d = ImageDraw.Draw(c); f = self.cap_font
            sp = d.textlength(" ", font=f); maxw = self.W * 0.84
            lines, cur, cw = [], [], 0
            for wd in words:
                ww = d.textlength(wd[0], font=f)
                if cur and cw + sp + ww > maxw: lines.append((cur, cw)); cur, cw = [], 0
                cw = cw + (sp if cur else 0) + ww; cur.append(wd)
            lines.append((cur, cw))
            k = ease_out((t - s) / 0.12)
            y = self.cap_y + (1 - k) * 18
            for ln, lw in lines:
                x = self.W / 2 - lw / 2
                for txt, ts in ln:
                    col = self.cap_hl if ts <= t else (255, 255, 255)
                    d.text((x, y), txt, font=f, fill=col + (int(255 * k),), stroke_width=7,
                           stroke_fill=(0, 0, 0, int(255 * k)), anchor="ls")
                    x += d.textlength(txt, font=f) + sp
                y += int(self.cap_size * 1.35)
            return

    @staticmethod
    def amount(ranges, t, fade=0.2):
        a = 0.0
        for s, e in ranges:
            a = max(a, clamp((t - s) / fade) * (1 - clamp((t - e) / fade)))
        return a

    def frame(self, t, base):
        bk = self.amount(self.p.get("blur", []), t)
        frame = base
        if bk > 0:
            frame = Image.blend(base.filter(ImageFilter.GaussianBlur(26 * bk)), Image.new("RGB", base.size, (4, 10, 30)), 0.38 * bk)
        gk = self.amount(self.p.get("grid", []), t)
        if gk > 0:
            frame = Image.blend(frame, self.grid, gk)
        c = frame.convert("RGBA")
        for i, e in enumerate(self.p.get("elements", [])):
            self.element(c, i, e, t)
        self.caption(c, t)
        return c.convert("RGB")


def sfx_times(plan):
    pops = [e["start"] for e in plan.get("elements", []) if e.get("sfx", True) and e["type"] != "counter"]
    pops += [it["at"] for e in plan.get("elements", []) if e["type"] == "checklist" for it in e["items"]]
    pops += [e["line2_at"] for e in plan.get("elements", []) if e["type"] == "title" and e.get("line2_at")]
    whoosh = [s for s, _ in plan.get("blur", []) + plan.get("grid", [])]
    return sorted(set(round(x, 2) for x in pops)), sorted(whoosh)


def build_audio(plan, plan_dir, src, out_wav, duration):
    ff = ffmpeg_exe(); T = tempfile.mkdtemp()
    run = lambda *a: subprocess.run([ff, "-v", "error", "-y", *a], check=True)
    run("-i", src, "-vn", "-af", "highpass=f=80,afftdn=nr=10:nf=-40,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,"
        "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "44100", "-ac", "2", f"{T}/voice.wav")
    run("-f", "lavfi", "-i", "aevalsrc='0.9*sin(2*PI*(1100-7000*t)*t)*exp(-t*38)':s=44100:d=0.12", "-ac", "2", f"{T}/pop.wav")
    run("-f", "lavfi", "-i", "anoisesrc=c=pink:a=0.5:d=0.35:r=44100", "-af",
        "bandpass=f=1800:w=1600,afade=t=in:d=0.2,afade=t=out:st=0.2:d=0.15", "-ac", "2", f"{T}/whoosh.wav")
    inputs, fc, mix = ["-i", f"{T}/voice.wav"], [], ["[0:a]"]
    pops, whooshes = sfx_times(plan) if plan.get("sfx", True) else ([], [])
    n = 1
    for p in pops:
        ms = max(0, int(p * 1000)); inputs += ["-i", f"{T}/pop.wav"]
        fc.append(f"[{n}:a]adelay={ms}|{ms},volume=0.22[s{n}]"); mix.append(f"[s{n}]"); n += 1
    for w in whooshes:
        ms = max(0, int((w - 0.12) * 1000)); inputs += ["-i", f"{T}/whoosh.wav"]
        fc.append(f"[{n}:a]adelay={ms}|{ms},volume=0.35[s{n}]"); mix.append(f"[s{n}]"); n += 1
    m = plan.get("music")
    if m:
        mp = m["path"] if os.path.isabs(m["path"]) else os.path.join(plan_dir, m["path"])
        inputs += ["-stream_loop", "-1", "-i", mp]
        vol = m.get("volume", 0.15)
        fc.append(f"[{n}:a]aresample=44100,aformat=channel_layouts=stereo,volume={vol},"
                  f"afade=t=out:st={max(0, duration - 1.5):.2f}:d=1.5[s{n}]"); mix.append(f"[s{n}]"); n += 1
    graph = ";".join(fc + ["".join(mix) + f"amix=inputs={n}:normalize=0:duration=first,alimiter=limit=0.89[a]"])
    run(*inputs, "-filter_complex", graph, "-map", "[a]", "-ar", "44100", out_wav)
    return out_wav


def main(plan_path, out):
    plan = json.load(open(plan_path, encoding="utf-8"))
    pdir = os.path.dirname(os.path.abspath(plan_path))
    src = plan["video"] if os.path.isabs(plan["video"]) else os.path.join(pdir, plan["video"])
    info = media_info(src)
    r = Renderer(plan, pdir)
    W, H, fps = r.W, r.H, r.fps
    ff = ffmpeg_exe()
    wav = build_audio(plan, pdir, src, tempfile.mktemp(suffix=".wav"), info["duration"] or 60)
    # fill the frame (cover-crop); crop_x shifts the horizontal crop (0 = left edge, 0.5 = centre, 1 = right edge)
    cx = plan.get("crop_x", 0.5)
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
          f"crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})/2")
    if plan.get("grade", True):
        vf += ",eq=contrast=1.05:saturation=1.08:brightness=0.01,unsharp=5:5:0.6"
    dec = subprocess.Popen([ff, "-v", "error", "-i", src, "-vf", vf, "-r", str(fps), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen([ff, "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                            "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium",
                            "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest",
                            "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n, size = 0, W * H * 3
    while True:
        buf = dec.stdout.read(size)
        if len(buf) < size: break
        enc.stdin.write(r.frame(n / fps, Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)).tobytes())
        n += 1
        if n % (fps * 5) == 0: print(f"  {n / fps:.0f}s rendered", file=sys.stderr)
    enc.stdin.close(); enc.wait(); dec.wait(); os.remove(wav)
    if enc.returncode: sys.exit("encode failed")
    print(f"done: {out} ({n} frames, {n / fps:.1f}s)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
