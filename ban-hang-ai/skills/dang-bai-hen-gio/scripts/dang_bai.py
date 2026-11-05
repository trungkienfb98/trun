"""Hẹn giờ đăng bài lên Fanpage Facebook của chính bạn bằng Graph API (tính năng hẹn giờ có sẵn của Facebook).

Bài được gửi lên Facebook ở trạng thái "đã lên lịch". Facebook tự đăng đúng giờ, máy bạn không cần bật.

Cách dùng:
  python dang_bai.py lich_dang.csv            # chạy thử: chỉ in kế hoạch, KHÔNG đăng
  python dang_bai.py lich_dang.csv --that     # gửi lịch lên Facebook thật

File CSV (UTF-8) gồm các cột: thoi_gian, noi_dung, anh_url, link
  thoi_gian: "2026-11-20 19:30" (giờ Việt Nam)
  anh_url:   link ảnh công khai (không bắt buộc)
  link:      link muốn gắn vào bài (không bắt buộc, không dùng chung với anh_url)

Cần biến môi trường FB_PAGE_ID và FB_PAGE_TOKEN (có thể để trong file .env cạnh script).
Token cần quyền pages_manage_posts và pages_read_engagement.
"""
import argparse
import csv
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

VN = timezone(timedelta(hours=7))
GRAPH_VERSION = os.environ.get("FB_GRAPH_VERSION", "v23.0")


def load_env() -> None:
    for p in (Path.cwd() / ".env", Path(__file__).resolve().parent / ".env"):
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.lstrip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def read_plan(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            text = (r.get("noi_dung") or "").strip()
            if not text:
                continue
            try:
                when = datetime.strptime(r["thoi_gian"].strip(), "%Y-%m-%d %H:%M").replace(tzinfo=VN)
            except (KeyError, ValueError):
                sys.exit(f"Dòng {i}: thoi_gian phải có dạng 2026-11-20 19:30")
            rows.append(
                {
                    "dong": i,
                    "luc": when,
                    "noi_dung": text,
                    "anh_url": (r.get("anh_url") or "").strip(),
                    "link": (r.get("link") or "").strip(),
                }
            )
    return sorted(rows, key=lambda x: x["luc"])


def check(rows: list[dict]) -> list[str]:
    now = datetime.now(VN)
    problems = []
    for r in rows:
        delta = r["luc"] - now
        if delta < timedelta(minutes=15):
            problems.append(f"Dòng {r['dong']}: giờ đăng phải sau hiện tại ít nhất 15 phút")
        elif delta > timedelta(days=29):
            problems.append(f"Dòng {r['dong']}: Facebook chỉ cho hẹn giờ tối đa khoảng 30 ngày")
        if r["anh_url"] and r["link"]:
            problems.append(f"Dòng {r['dong']}: chọn anh_url HOẶC link, không dùng cả hai")
    gaps = [b["luc"] - a["luc"] for a, b in zip(rows, rows[1:])]
    if any(g < timedelta(hours=2) for g in gaps):
        problems.append("Cảnh báo: có bài cách nhau dưới 2 giờ. Đăng dày quá dễ làm giảm tiếp cận.")
    return problems


def schedule(row: dict, page_id: str, token: str) -> str:
    base = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}"
    data = {
        "published": "false",
        "scheduled_publish_time": str(int(row["luc"].timestamp())),
        "access_token": token,
    }
    if row["anh_url"]:
        url, data["url"], data["caption"] = f"{base}/photos", row["anh_url"], row["noi_dung"]
    else:
        url, data["message"] = f"{base}/feed", row["noi_dung"]
        if row["link"]:
            data["link"] = row["link"]
    r = httpx.post(url, data=data, timeout=60)
    body = r.json()
    if r.status_code >= 400 or "error" in body:
        raise RuntimeError(body.get("error", {}).get("message", r.text))
    return body.get("post_id") or body.get("id", "")


def main() -> None:
    ap = argparse.ArgumentParser(description="Hẹn giờ đăng bài lên Fanpage")
    ap.add_argument("csv")
    ap.add_argument("--that", action="store_true", help="gửi lịch lên Facebook thật")
    args = ap.parse_args()

    load_env()
    rows = read_plan(args.csv)
    if not rows:
        sys.exit("File không có bài nào.")
    problems = check(rows)
    for p in problems:
        print("⚠️ ", p)
    if any(not p.startswith("Cảnh báo") for p in problems):
        sys.exit("Sửa các lỗi trên rồi chạy lại.")

    for r in rows:
        kind = "ảnh" if r["anh_url"] else ("link" if r["link"] else "chữ")
        print(f"🗓  {r['luc']:%d/%m %H:%M} [{kind}] {r['noi_dung'][:70].replace(chr(10), ' ')}…")
    if not args.that:
        print(f"\nChạy thử: {len(rows)} bài. Thêm --that để gửi lịch lên Facebook.")
        return

    page_id, token = os.environ.get("FB_PAGE_ID"), os.environ.get("FB_PAGE_TOKEN")
    if not (page_id and token):
        sys.exit("Thiếu FB_PAGE_ID hoặc FB_PAGE_TOKEN.")
    ok = 0
    for r in rows:
        try:
            pid = schedule(r, page_id, token)
            ok += 1
            print(f"✅ Dòng {r['dong']}: đã lên lịch ({pid})")
        except (RuntimeError, httpx.HTTPError) as e:
            print(f"❌ Dòng {r['dong']}: {e}")
    print(f"\nXong: {ok}/{len(rows)} bài. Xem lại trong Meta Business Suite → Lịch.")


if __name__ == "__main__":
    main()
