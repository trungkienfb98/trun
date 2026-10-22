"""Shared helpers: locate ffmpeg (system or pip imageio-ffmpeg) and read media info."""
import re
import shutil
import subprocess
import sys


def ffmpeg_exe():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"], check=True)
        import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def media_info(path):
    """Return dict(width, height, fps, duration, has_audio) parsed from `ffmpeg -i`."""
    err = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    info = {"width": None, "height": None, "fps": 30.0, "duration": None, "has_audio": "Audio:" in err}
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    if m:
        info["duration"] = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", err)
    if m:
        info["width"], info["height"] = int(m[1]), int(m[2])
    m = re.search(r"([\d.]+) fps", err)
    if m:
        info["fps"] = float(m[1])
    # phone videos often carry a rotation flag; ffmpeg auto-rotates, so swap dims to match
    if re.search(r"rotation of -?90|rotate\s*:\s*-?(90|270)", err) and info["width"]:
        info["width"], info["height"] = info["height"], info["width"]
    return info


if __name__ == "__main__":
    print(media_info(sys.argv[1]))
