import argparse
import csv
import json
import os
import shutil
from pathlib import Path


FOLDERS = [
    "01_VIDEO_GOC", "02_NHAC_NEN", "03_LOGO", "04_NOI_DUNG",
    "05_VIDEO_DA_XU_LY", "06_ANH_XEM_TRUOC", "07_NHAT_KY",
    "08_PHAN_TICH_KENH"
]


def main():
    parser = argparse.ArgumentParser(description="Initialize a portable Reel workspace")
    parser.add_argument("--root", required=True)
    parser.add_argument("--brand-name", required=True)
    parser.add_argument("--reference-url")
    parser.add_argument("--destination-url")
    parser.add_argument("--open", action="store_true", dest="open_folder")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    for folder in FOLDERS:
        (root / folder).mkdir(exist_ok=True)

    default_path = Path(__file__).resolve().parent.parent / "assets" / "default-config.json"
    config = json.loads(default_path.read_text(encoding="utf-8"))
    config.update({
        "brand_name": args.brand_name,
        "reference_channel_url": args.reference_url,
        "destination_page_url": args.destination_url,
    })
    (root / "BRAND_CONFIG.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ledgers = {
        "media_usage.csv": ["kind", "file", "status", "use_count", "last_content", "last_used"],
        "publishing_schedule.csv": ["content_id", "page", "video", "date", "time", "timezone", "status", "platform_id"],
    }
    for name, header in ledgers.items():
        path = root / "07_NHAT_KY" / name
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                csv.writer(f).writerow(header)

    analysis = root / "08_PHAN_TICH_KENH" / "reference_analysis.json"
    if not analysis.exists():
        analysis.write_text(json.dumps({"channel": args.reference_url, "facts": [], "inferences": [], "posts": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.open_folder:
        os.startfile(root)
    print(json.dumps({"workspace": str(root), "config": str(root / "BRAND_CONFIG.json")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
