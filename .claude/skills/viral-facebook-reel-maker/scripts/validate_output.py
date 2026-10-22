import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Validate technical Reel properties")
    parser.add_argument("--video", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--tolerance", type=float, default=0.2)
    args = parser.parse_args()
    if not shutil.which("ffprobe"):
        raise SystemExit("FFprobe must be available on PATH")
    video = Path(args.video).expanduser().resolve()
    raw = subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video)], text=True, encoding="utf-8")
    data = json.loads(raw)
    streams = data.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(data.get("format", {}).get("duration", 0))
    checks = {
        "file_exists": video.exists() and video.stat().st_size > 0,
        "duration": abs(duration - args.duration) <= args.tolerance,
        "vertical_1080x1920": bool(v and v.get("width") == 1080 and v.get("height") == 1920),
        "h264_video": bool(v and v.get("codec_name") == "h264"),
        "audio_present": a is not None,
    }
    result = {"ok": all(checks.values()), "checks": checks, "actual_duration": duration, "video": str(video)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
