import argparse
import csv
import json
from pathlib import Path


KINDS = {
    "video": ("01_VIDEO_GOC", {".mp4", ".mov", ".mkv", ".webm", ".avi"}),
    "music": ("02_NHAC_NEN", {".mp3", ".wav", ".m4a", ".aac", ".flac"}),
    "logo": ("03_LOGO", {".png", ".webp", ".jpg", ".jpeg"}),
}


def read_usage(path):
    result = {}
    if not path.exists():
        return result
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            result[(row.get("kind", ""), row.get("file", ""))] = row
    return result


def main():
    parser = argparse.ArgumentParser(description="Select least-used eligible media")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--kind", required=True, choices=KINDS)
    parser.add_argument("--exclude")
    args = parser.parse_args()

    root = Path(args.workspace).expanduser().resolve()
    folder, extensions = KINDS[args.kind]
    assets = sorted(p for p in (root / folder).iterdir() if p.is_file() and p.suffix.lower() in extensions)
    usage = read_usage(root / "07_NHAT_KY" / "media_usage.csv")
    eligible = []
    for path in assets:
        rel = path.relative_to(root).as_posix()
        row = usage.get((args.kind, rel), {})
        if row.get("status") == "blocked" or rel == args.exclude:
            continue
        eligible.append((int(row.get("use_count") or 0), row.get("last_used") or "", rel, path))
    if not eligible:
        raise SystemExit(f"No eligible {args.kind} found in {root / folder}")
    eligible.sort(key=lambda x: (x[0], x[1], x[2].lower()))
    count, last_used, rel, path = eligible[0]
    print(json.dumps({"kind": args.kind, "file": rel, "absolute_path": str(path), "use_count": count, "last_used": last_used}, ensure_ascii=False))


if __name__ == "__main__":
    main()
