"""Luồng xử lý chung cho mọi kênh: nhận tin khách, hỏi AI, ghi đơn, chuyển người thật."""
import logging

import httpx

import brain
import config
import store

log = logging.getLogger("engine")
REQUIRED = ["ten", "sdt", "dia_chi", "san_pham"]


def _notify(payload: dict) -> None:
    """Báo cho chủ shop qua webhook (Google Sheets, Telegram bot, n8n...). Không bắt buộc."""
    if not config.ORDER_WEBHOOK_URL:
        return
    try:
        httpx.post(config.ORDER_WEBHOOK_URL, json=payload, timeout=10, follow_redirects=True)
    except httpx.HTTPError as e:
        log.warning("Không gửi được webhook báo đơn: %s", e)


def staff_replied(channel: str, user_id: str, text: str) -> None:
    """Nhân viên tự nhắn cho khách → ghi lại và cho bot nghỉ với khách này."""
    store.add_message(channel, user_id, "staff", text)
    store.pause(channel, user_id, config.HANDOFF_HOURS)


def handle_customer_message(channel: str, user_id: str, text: str, name: str = "") -> list[str]:
    """Trả về danh sách tin cần gửi lại cho khách (rỗng = không gửi gì)."""
    text = (text or "").strip()
    if not text:
        return []
    store.add_message(channel, user_id, "user", text)

    if text.lower() in {"#bot", "/bot"}:  # nhân viên gõ để bật lại bot cho khách này
        store.resume(channel, user_id)
        return []
    if store.is_paused(channel, user_id):
        return []

    history = store.history(channel, user_id, config.HISTORY_TURNS)
    draft = store.get_draft_order(channel, user_id)
    result = brain.think(history, draft)
    if not result:
        return []

    # Gộp thông tin đơn: chỉ ghi đè trường mới khi AI trả về giá trị khác rỗng.
    order = dict(draft)
    for k, v in (result.get("don_hang") or {}).items():
        if v and str(v).strip():
            order[k] = str(v).strip()
    if name and not order.get("ten_tai_khoan"):
        order["ten_tai_khoan"] = name
    store.save_draft_order(channel, user_id, order)

    if result.get("da_xac_nhan_don") and all(order.get(f) for f in REQUIRED):
        order_id = store.save_order(channel, user_id, order)
        log.info("Đơn mới #%s từ %s/%s", order_id, channel, user_id)
        _notify({"loai": "don_hang", "ma": order_id, "kenh": channel, "khach": user_id, **order})

    if result.get("chuyen_nguoi_that"):
        store.pause(channel, user_id, config.HANDOFF_HOURS)
        _notify(
            {
                "loai": "chuyen_nguoi_that",
                "kenh": channel,
                "khach": user_id,
                "ten": name,
                "ly_do": result.get("ly_do_chuyen", ""),
                "tin_cuoi": text,
            }
        )

    reply = (result.get("tra_loi") or "").strip()
    if not reply:
        return []
    store.add_message(channel, user_id, "assistant", reply)
    # Tách thành vài tin ngắn cho giống người nhắn (tối đa 3 tin).
    parts = [p.strip() for p in reply.split("\n\n") if p.strip()]
    if len(parts) > 3:
        parts = parts[:2] + ["\n\n".join(parts[2:])]
    return [p[:1900] for p in parts]
