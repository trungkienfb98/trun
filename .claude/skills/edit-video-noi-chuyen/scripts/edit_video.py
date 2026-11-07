#!/usr/bin/env python3
"""
Edit video "nói chuyện vào camera" theo phong cách review tuyển dụng
(mẫu: "Review Yamanashi"):

  1. Cắt khoảng lặng (jump cut), giữ nhịp nói liền mạch
  2. (tuỳ chọn) Zoom xen kẽ 100% / 108% giữa các đoạn để che vết giật
  3. Phụ đề hộp vàng bo tròn #FFDC00, chữ đen, căn giữa, tâm ~78% chiều cao
  4. (tuỳ chọn) Tiêu đề hook ở 3 giây đầu + khung CTA ở cuối video
  5. Chuẩn hoá âm lượng -14 LUFS (chuẩn TikTok / Reels)

Chỉ cần: ffmpeg, ffprobe, Python 3 + Pillow.

Ví dụ:
  # Bước 1: chỉ cắt khoảng lặng
  python3 edit_video.py cut in.mp4 cut.mp4 --zoom
  # Bước 2: dựng bản cuối với phụ đề (SRT khớp thời gian của cut.mp4)
  python3 edit_video.py render cut.mp4 final.mp4 --srt cut.srt \
      --hook "LƯƠNG 21 TRIỆU|Tuyển 2 kỹ sư đi Nhật" \
      --cta "Inbox chị Hằng để được hỗ trợ"
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------- style ----
# Thông số đo trực tiếp từ video mẫu 1080x1920 (tỉ lệ theo chiều cao/rộng)
STYLE = {
    "box_color": (255, 220, 0, 255),     # #FFDC00
    "text_color": (0, 0, 0, 255),
    "font_px": 0.029,       # ~56px / 1920
    "line_gap": 1.18,       # khoảng cách dòng
    "pad_x": 0.030,         # 32px / 1080
    "pad_y": 0.019,         # ~36px / 1920
    "radius": 0.024,        # ~26px / 1080
    "max_w": 0.86,          # hộp rộng tối đa ~920px / 1080
    "center_y": 0.783,      # tâm hộp ~1504 / 1920
    "max_lines": 2,
}

FONT_CANDIDATES = [
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    "C:/Windows/Fonts/arialbd.ttf",
]


def die(msg):
    sys.exit(f"[edit_video] LỖI: {msg}")


def run(cmd, capture=False):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die("lệnh thất bại:\n  " + " ".join(cmd) + "\n" + r.stderr[-2000:])
    return r.stderr if capture else None


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format",
         "-show_streams", path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    w, h = int(v["width"]), int(v["height"])
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = abs(int(sd["rotation"]))
    if rot in (90, 270):
        w, h = h, w
    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    return {"w": w, "h": h, "fps": fps, "dur": float(j["format"]["duration"])}


def find_font(user_font):
    if user_font:
        if not os.path.exists(user_font):
            die(f"không thấy font {user_font}")
        return user_font
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    die("không tìm thấy font có dấu tiếng Việt, hãy truyền --font /đường/dẫn/font.ttf")


# ------------------------------------------------------------ 1. cut ------
def detect_speech(path, noise_db, min_silence, pad, dur):
    log = run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
               f"silencedetect=n={noise_db}dB:d={min_silence}", "-f", "null", "-"],
              capture=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    if len(ends) < len(starts):
        ends.append(dur)
    keep, t = [], 0.0
    for s, e in zip(starts, ends):
        a, b = t, min(s + pad, dur)
        if b - a > 0.12:
            keep.append([a, b])
        t = max(e - pad, 0.0)
    if dur - t > 0.12:
        keep.append([t, dur])
    # gộp các đoạn chồng nhau do padding
    merged = []
    for a, b in keep:
        if merged and a <= merged[-1][1] + 0.02:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def cmd_cut(a):
    info = probe(a.input)
    segs = detect_speech(a.input, a.noise, a.min_silence, a.pad, info["dur"])
    if not segs:
        die("không phát hiện được giọng nói, thử giảm --noise (vd -40)")
    W, H = info["w"], info["h"]
    parts, labels = [], []
    for i, (s, e) in enumerate(segs):
        v = f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS"
        if a.zoom and i % 2 == 1:
            z = a.zoom_level
            v += (f",scale=iw*{z}:ih*{z},crop={W}:{H}:(iw-{W})/2:(ih-{H})/2*0.6")
        v += f",setsar=1[v{i}]"
        parts += [v, f"[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}]"]
        labels.append(f"[v{i}][a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + \
        f"concat=n={len(segs)}:v=1:a=1[v][a]"
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(fc)
        fcfile = f.name
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.input,
         "-filter_complex_script", fcfile, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", a.output])
    os.unlink(fcfile)
    new = sum(e - s for s, e in segs)
    print(f"[cut] {len(segs)} đoạn giữ lại | {info['dur']:.1f}s -> {new:.1f}s "
          f"(bỏ {info['dur'] - new:.1f}s khoảng lặng)")
    if a.segments:
        with open(a.segments, "w") as f:
            json.dump(segs, f, indent=1)


# ------------------------------------------------------- 2. captions ------
def parse_srt(path):
    txt = open(path, encoding="utf-8-sig").read().replace("\r", "")
    cues = []
    for block in re.split(r"\n\s*\n", txt.strip()):
        lines = block.strip().split("\n")
        tl = next((i for i, l in enumerate(lines) if "-->" in l), None)
        if tl is None:
            continue
        def ts(x):
            h, m, s = x.strip().replace(",", ".").split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
        a, b = lines[tl].split("-->")
        text = " ".join(l.strip() for l in lines[tl + 1:] if l.strip())
        if text:
            cues.append((ts(a), ts(b), text))
    return cues


def wrap(draw, text, font, max_w, max_lines):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def pill_png(text, W, H, font_path, out, style=STYLE, scale=1.0,
             box=None, color=None):
    from PIL import Image, ImageDraw, ImageFont
    # bỏ emoji / ký tự ngoài BMP: font thường không vẽ được, sẽ thành ô vuông
    text = "".join(ch for ch in text if ord(ch) < 0x2000 or 0x20A0 <= ord(ch) < 0x2400).strip()
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad_x, pad_y = int(W * style["pad_x"]), int(H * style["pad_y"])
    fs = int(H * style["font_px"] * scale)
    while True:  # câu quá dài -> thu nhỏ chữ cho vừa tối đa max_lines dòng
        font = ImageFont.truetype(font_path, fs)
        lines = wrap(d, text, font, W * style["max_w"] - 2 * pad_x, style["max_lines"])
        if len(lines) <= style["max_lines"] or fs < H * 0.016:
            break
        fs = int(fs * 0.92)
    lh = int(fs * style["line_gap"])
    asc, desc = font.getmetrics()
    tw = max(d.textlength(l, font=font) for l in lines)
    th = lh * (len(lines) - 1) + asc + desc
    bw, bh = int(tw + 2 * pad_x), int(th + 2 * pad_y)
    cy = int(H * (style["center_y"] if box is None else box))
    x0, y0 = (W - bw) // 2, cy - bh // 2
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], radius=int(W * style["radius"]),
                        fill=color or style["box_color"])
    for i, l in enumerate(lines):
        lw = d.textlength(l, font=font)
        d.text(((W - lw) / 2, y0 + pad_y + i * lh), l, font=font,
               fill=style["text_color"])
    img.save(out)


def cmd_render(a):
    info = probe(a.input)
    W, H, dur = info["w"], info["h"], info["dur"]
    font = find_font(a.font)
    tmp = tempfile.mkdtemp(prefix="edit_video_")
    overlays = []  # (png, start, end)
    if a.srt:
        for i, (s, e, t) in enumerate(parse_srt(a.srt)):
            p = os.path.join(tmp, f"cap_{i:04d}.png")
            pill_png(t, W, H, font, p)
            overlays.append((p, s, e))
    if a.hook:
        # "DÒNG TO|dòng phụ" -> hai hộp ở 1/5 trên màn hình
        big, _, small = a.hook.partition("|")
        p = os.path.join(tmp, "hook1.png")
        pill_png(big.strip(), W, H, font, p, scale=1.6, box=0.17)
        overlays.append((p, 0, a.hook_sec))
        if small.strip():
            p = os.path.join(tmp, "hook2.png")
            pill_png(small.strip(), W, H, font, p, scale=1.05, box=0.235,
                     color=(255, 255, 255, 255))
            overlays.append((p, 0, a.hook_sec))
    if a.cta:
        p = os.path.join(tmp, "cta.png")
        pill_png(a.cta, W, H, font, p, scale=1.15, box=0.17)
        overlays.append((p, max(0, dur - a.cta_sec), dur + 1))

    inputs, chain, last = ["-i", a.input], [], "[0:v]"
    for i, (p, s, e) in enumerate(overlays):
        inputs += ["-loop", "1", "-t", f"{dur:.3f}", "-i", p]
        out = f"[o{i}]"
        chain.append(f"{last}[{i + 1}:v]overlay=0:0:enable='between(t,{s:.3f},{e:.3f})'{out}")
        last = out
    vf = ";".join(chain) + (";" if chain else "") + f"{last}format=yuv420p[v]"
    af = "loudnorm=I=-14:TP=-1.5:LRA=11" if not a.no_loudnorm else "anull"
    fcfile = os.path.join(tmp, "fc.txt")
    open(fcfile, "w").write(vf + f";[0:a]{af}[a]")
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs,
         "-filter_complex_script", fcfile, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", "30",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-movflags", "+faststart", "-shortest", a.output])
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[render] xong: {a.output} ({len(overlays)} lớp chữ, font {os.path.basename(font)})")


def fmt_ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def cmd_split_srt(a):
    """Chia câu dài thành các cụm ngắn (mặc định <= 8 từ, ~1.5-2s/cụm như video mẫu)."""
    out = []
    for s, e, t in parse_srt(a.input):
        words = t.split()
        n = max(1, -(-len(words) // a.max_words))       # số cụm, làm tròn lên
        size = -(-len(words) // n)
        chunks = [words[i:i + size] for i in range(0, len(words), size)]
        total = sum(len(" ".join(c)) for c in chunks)
        cur = s
        for c in chunks:                                # chia thời gian theo số ký tự
            d = (e - s) * len(" ".join(c)) / total
            out.append((cur, cur + d, " ".join(c)))
            cur += d
    with open(a.output, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(out, 1):
            f.write(f"{i}\n{fmt_ts(s)} --> {fmt_ts(e)}\n{t}\n\n")
    print(f"[split-srt] {len(out)} câu -> {a.output}")


def cmd_preview(a):
    """Xuất 1 ảnh PNG xem thử hộp phụ đề, không cần video."""
    font = find_font(a.font)
    from PIL import Image
    W, H = 1080, 1920
    pill_png(a.text, W, H, font, a.output)
    bg = Image.new("RGBA", (W, H), (120, 120, 120, 255))
    bg.alpha_composite(Image.open(a.output))
    bg.convert("RGB").save(a.output)
    print(f"[preview] {a.output}")


def main():
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            die(f"chưa cài {tool} (macOS: brew install ffmpeg)")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("cut", help="cắt khoảng lặng")
    c.add_argument("input"); c.add_argument("output")
    c.add_argument("--noise", type=float, default=-35, help="ngưỡng im lặng dB (mặc định -35)")
    c.add_argument("--min-silence", type=float, default=0.35, help="khoảng lặng tối thiểu để cắt (giây)")
    c.add_argument("--pad", type=float, default=0.08, help="giữ lại trước/sau mỗi câu (giây)")
    c.add_argument("--zoom", action="store_true", help="zoom xen kẽ để che vết giật")
    c.add_argument("--zoom-level", type=float, default=1.08)
    c.add_argument("--segments", help="lưu danh sách đoạn giữ lại ra file JSON")
    c.set_defaults(fn=cmd_cut)

    r = sub.add_parser("render", help="gắn phụ đề, hook, CTA, chuẩn hoá âm thanh")
    r.add_argument("input"); r.add_argument("output")
    r.add_argument("--srt", help="file phụ đề SRT (thời gian theo video input)")
    r.add_argument("--hook", help='tiêu đề 3s đầu, dạng "DÒNG TO|dòng phụ"')
    r.add_argument("--hook-sec", type=float, default=3.0)
    r.add_argument("--cta", help="chữ kêu gọi hành động ở cuối video")
    r.add_argument("--cta-sec", type=float, default=3.0)
    r.add_argument("--font", help="đường dẫn font .ttf/.otf có dấu tiếng Việt")
    r.add_argument("--no-loudnorm", action="store_true")
    r.set_defaults(fn=cmd_render)

    s = sub.add_parser("split-srt", help="chia câu phụ đề dài thành cụm ngắn")
    s.add_argument("input"); s.add_argument("output")
    s.add_argument("--max-words", type=int, default=8)
    s.set_defaults(fn=cmd_split_srt)

    p = sub.add_parser("preview", help="ảnh xem thử phụ đề")
    p.add_argument("text"); p.add_argument("output")
    p.add_argument("--font")
    p.set_defaults(fn=cmd_preview)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
