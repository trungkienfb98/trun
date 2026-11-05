"""Chat thử với bot ngay trên máy tính, không cần Facebook/Zalo.

Chạy:  python chat_thu.py
Gõ tin như khách hàng. Gõ /don để xem đơn đang ghi nhận, /moi để bắt đầu khách mới, /thoat để thoát.
"""
import json
import uuid

import engine
import store

CHANNEL = "thu_nghiem"


def main() -> None:
    user = uuid.uuid4().hex[:8]
    print("🤖 Bot bán hàng — chế độ thử. Bạn đóng vai khách. (/don /moi /thoat)\n")
    while True:
        try:
            text = input("👤 Khách: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/thoat":
            break
        if text == "/moi":
            user = uuid.uuid4().hex[:8]
            print("— Khách mới —\n")
            continue
        if text == "/don":
            print(json.dumps(store.get_draft_order(CHANNEL, user), ensure_ascii=False, indent=2))
            continue
        parts = engine.handle_customer_message(CHANNEL, user, text)
        if not parts and store.is_paused(CHANNEL, user):
            print("   (bot đã chuyển cho nhân viên — gõ /bot để bật lại)\n")
            continue
        for p in parts:
            print(f"🛍️  Shop: {p}")
        print()


if __name__ == "__main__":
    main()
