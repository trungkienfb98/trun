"""Remove pauses longer than --min-silence seconds (jump cuts, like the sample video).

Usage: python3 jumpcut.py <in.mp4> <out.mp4> [--min-silence 0.35] [--threshold -35] [--keep 0.08]

Run this BEFORE transcribe.py so word timestamps match the cut video.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_exe, media_info  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--min-silence", type=float, default=0.35)
    ap.add_argument("--threshold", type=float, default=-35)
    ap.add_argument("--keep", type=float, default=0.08, help="seconds of pause kept at each cut edge")
    a = ap.parse_args()
    ff = ffmpeg_exe(); dur = media_info(a.src)["duration"]
    err = subprocess.run([ff, "-hide_banner", "-i", a.src, "-vn", "-af",
                          f"silencedetect=n={a.threshold}dB:d={a.min_silence}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)] + [dur]
    keep, cur = [], 0.0
    for s, e in zip(starts, ends):
        if s - cur > 0.05: keep.append((cur, min(dur, s + a.keep)))
        cur = max(cur, e - a.keep)
    if dur - cur > 0.05: keep.append((cur, dur))
    if not keep: sys.exit("no speech found")
    parts = "".join(f"[0:v]trim={s:.3f}:{e:.3f},setpts=PTS-STARTPTS[v{i}];[0:a]atrim={s:.3f}:{e:.3f},asetpts=PTS-STARTPTS[a{i}];"
                    for i, (s, e) in enumerate(keep))
    parts += "".join(f"[v{i}][a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=1[v][a]"
    subprocess.run([ff, "-v", "error", "-y", "-i", a.src, "-filter_complex", parts, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "17", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", a.out], check=True)
    total = sum(e - s for s, e in keep)
    print(f"kept {len(keep)} segments: {dur:.1f}s -> {total:.1f}s")


if __name__ == "__main__":
    main()
