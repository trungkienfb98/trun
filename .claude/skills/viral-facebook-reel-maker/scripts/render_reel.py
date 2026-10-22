import argparse
import csv
import datetime as dt
import json
import re
import shutil
import subprocess
import textwrap
from pathlib import Path


def ass_color(hex_color):
    value = hex_color.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Invalid color: {hex_color}")
    r, g, b = value[0:2], value[2:4], value[4:6]
    return f"&H00{b}{g}{r}"


def ass_escape(value):
    return value.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def wrap_text(value, width):
    lines = []
    for paragraph in value.splitlines() or [""]:
        wrapped = textwrap.wrap(paragraph, width=width, break_long_words=False, break_on_hyphens=False) or [""]
        lines.extend(wrapped)
    return "\\N".join(ass_escape(line) for line in lines)


def highlight(text, phrases, color):
    for phrase in sorted((p for p in phrases if p), key=len, reverse=True):
        escaped = ass_escape(phrase)
        text = re.sub(re.escape(escaped), lambda m: "{\\c" + color + "}" + m.group(0) + "{\\c&H00FFFFFF}", text, flags=re.IGNORECASE)
    return text


def resolve(root, value, folder, extensions):
    if value:
        p = Path(value)
        p = p if p.is_absolute() else root / p
        if not p.exists():
            raise FileNotFoundError(p)
        return p.resolve()
    choices = sorted(p for p in (root / folder).iterdir() if p.is_file() and p.suffix.lower() in extensions)
    if not choices:
        raise FileNotFoundError(f"No media in {root / folder}")
    return choices[0].resolve()


def log_usage(root, kind, path, content_id):
    ledger = root / "07_NHAT_KY" / "media_usage.csv"
    rows = []
    if ledger.exists():
        with ledger.open("r", newline="", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    found = False
    for row in rows:
        if row.get("kind") == kind and row.get("file") == rel:
            row.update(status="used", use_count=str(int(row.get("use_count") or 0) + 1), last_content=content_id, last_used=dt.date.today().isoformat())
            found = True
    if not found:
        rows.append({"kind": kind, "file": rel, "status": "used", "use_count": "1", "last_content": content_id, "last_used": dt.date.today().isoformat()})
    with ledger.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["kind", "file", "status", "use_count", "last_content", "last_used"])
        writer.writeheader(); writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Render a fixed-text vertical Reel with FFmpeg")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--content", required=True)
    args = parser.parse_args()

    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("FFmpeg and FFprobe must be available on PATH")
    root = Path(args.workspace).expanduser().resolve()
    config = json.loads((root / "BRAND_CONFIG.json").read_text(encoding="utf-8"))
    content_path = Path(args.content).expanduser().resolve()
    content = json.loads(content_path.read_text(encoding="utf-8"))
    video = resolve(root, content.get("video_file"), "01_VIDEO_GOC", {".mp4", ".mov", ".mkv", ".webm", ".avi"})
    music = resolve(root, content.get("music_file"), "02_NHAC_NEN", {".mp3", ".wav", ".m4a", ".aac", ".flac"})
    logo = resolve(root, content.get("logo_file"), "03_LOGO", {".png", ".webp", ".jpg", ".jpeg"}) if content.get("logo_file") else None
    duration = float(config.get("video_duration_seconds", 20))
    speed = float(config.get("footage_speed", 0.5))
    width, height = int(config.get("output_width", 1080)), int(config.get("output_height", 1920))
    fps = int(config.get("fps", 30))
    output_dir = root / "05_VIDEO_DA_XU_LY"; output_dir.mkdir(exist_ok=True)
    preview_dir = root / "06_ANH_XEM_TRUOC"; preview_dir.mkdir(exist_ok=True)
    content_id = re.sub(r"[^A-Za-z0-9_-]+", "_", content.get("id") or content_path.stem)
    output = output_dir / f"{content_id}.mp4"
    ass_file = output_dir / f"{content_id}.ass"

    title = wrap_text(content.get("title", ""), 25)
    body = wrap_text(content.get("body", ""), 38)
    hi_color = ass_color(config.get("highlight_color", "#DFFF00"))
    title = highlight(title, content.get("highlights", []), hi_color)
    body = highlight(body, content.get("highlights", []), hi_color)
    font = content.get("font_name", "Arial")
    title_size = int(content.get("title_font_size", 70)); body_size = int(content.get("body_font_size", 45))
    ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Title,{font},{title_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,8,76,76,650,1
Style: Body,{font},{body_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,8,90,90,930,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
Dialogue: 0,0:00:00.00,0:59:59.00,Title,,0,0,0,,{title}
Dialogue: 0,0:00:00.00,0:59:59.00,Body,,0,0,0,,{body}
"""
    ass_file.write_text(ass, encoding="utf-8-sig")

    dark = float(config.get("background_brightness", -0.24)); blur = float(config.get("background_blur_sigma", 0.8))
    filters = [f"[0:v]setpts=PTS/{speed},scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},gblur=sigma={blur},eq=brightness={dark}:contrast=1.02[base]"]
    inputs = ["-stream_loop", "-1", "-i", str(video), "-stream_loop", "-1", "-i", str(music)]
    if logo:
        inputs += ["-loop", "1", "-i", str(logo)]
        logo_y = int(content.get("logo_y", 280))
        filters += ["[2:v]scale=96:96:force_original_aspect_ratio=decrease[logo]", f"[base][logo]overlay=(W-w)/2:{logo_y}[branded]", f"[branded]ass={ass_file.name}[v]"]
    else:
        filters += [f"[base]ass={ass_file.name}[v]"]
    fade_start = max(0, duration - 1)
    filters += [f"[1:a]volume={float(config.get('music_volume', 0.42))},afade=t=out:st={fade_start}:d=1[a]"]
    command = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]", "-t", str(duration), "-r", str(fps), "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    subprocess.run(command, cwd=output_dir, check=True)
    for frac, suffix in [(0.25, "25"), (0.5, "50"), (0.75, "75")]:
        preview = preview_dir / f"{content_id}_{suffix}.png"
        subprocess.run(["ffmpeg", "-y", "-ss", str(duration * frac), "-i", str(output), "-frames:v", "1", str(preview)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log_usage(root, "video", video, content_id); log_usage(root, "music", music, content_id)
    if logo: log_usage(root, "logo", logo, content_id)
    print(json.dumps({"video": str(output), "previews": str(preview_dir), "content_id": content_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
