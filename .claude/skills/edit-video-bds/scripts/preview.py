"""Grab frames from a rendered video to check layout (overlaps, clipped diacritics, faces covered).

Usage:
  python3 preview.py <video> <out.jpg>                 # contact sheet, 2 frames/s
  python3 preview.py <video> <out.jpg> 2.3 4.7 8.6     # side-by-side frames at these seconds
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ffmpeg_exe, media_info  # noqa: E402


def main(video, out, times):
    ff = ffmpeg_exe()
    if not times:
        dur = media_info(video)["duration"] or 10
        rows = max(1, int(dur * 2 / 10 + 0.999))
        subprocess.run([ff, "-v", "error", "-y", "-i", video, "-vf", f"fps=2,scale=216:-1,tile=10x{rows}",
                        "-frames:v", "1", out], check=True)
    else:
        args, n = [], len(times)
        for t in times: args += ["-ss", str(t), "-i", video]
        graph = "".join(f"[{i}:v]trim=end_frame=1,scale=360:-1[v{i}];" for i in range(n))
        graph += "".join(f"[v{i}]" for i in range(n)) + (f"hstack={n}" if n > 1 else "copy")
        subprocess.run([ff, "-v", "error", "-y", *args, "-filter_complex", graph, "-frames:v", "1", out], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
