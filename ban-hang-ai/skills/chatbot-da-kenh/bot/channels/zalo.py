"""Zalo Official Account (OA): nhận tin qua webhook, trả lời bằng Tin Tư vấn (message/cs).

Lưu ý của Zalo: OA chỉ nhắn tư vấn miễn phí cho người đã tương tác trong khung thời gian cho phép
(thường là 7 ngày sau tin cuối của khách). Xem chính sách hiện hành tại developers.zalo.me.
"""
import hashlib
import json
import logging

import httpx

import config

log = logging.getLogger("zalo")
CHANNEL = "zalo"
SEND_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"
TOKEN_URL = "https://oauth.zaloapp.com/v4/oa/access_token"
TOKEN_FILE = config.BASE_DIR / "zalo_tokens.json"

_tokens = {"access_token": config.ZALO_ACCESS_TOKEN, "refresh_token": config.ZALO_REFRESH_TOKEN}
if TOKEN_FILE.exists():  # token mới nhất sau lần làm mới gần nhất
    _tokens.update(json.loads(TOKEN_FILE.read_text()))


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    """Zalo ký: X-ZEvent-Signature = "mac=" + sha256(app_id + body + timestamp + OA secret key)."""
    if not config.ZALO_OA_SECRET:
        log.warning("Chưa đặt ZALO_OA_SECRET — bỏ qua kiểm tra chữ ký (KHÔNG nên dùng khi chạy thật)")
        return True
    try:
        timestamp = str(json.loads(raw_body).get("timestamp", ""))
    except json.JSONDecodeError:
        return False
    data = config.ZALO_APP_ID + raw_body.decode("utf-8") + timestamp + config.ZALO_OA_SECRET
    expected = "mac=" + hashlib.sha256(data.encode("utf-8")).hexdigest()
    return bool(header) and header.strip() == expected


def _refresh_token() -> bool:
    if not (_tokens.get("refresh_token") and config.ZALO_APP_SECRET):
        log.error("Access token Zalo hết hạn, thiếu ZALO_REFRESH_TOKEN/ZALO_APP_SECRET để làm mới")
        return False
    r = httpx.post(
        TOKEN_URL,
        headers={"secret_key": config.ZALO_APP_SECRET},
        data={
            "refresh_token": _tokens["refresh_token"],
            "app_id": config.ZALO_APP_ID,
            "grant_type": "refresh_token",
        },
        timeout=20,
    )
    data = r.json()
    if "access_token" not in data:
        log.error("Làm mới token Zalo thất bại: %s", data)
        return False
    # Refresh token của Zalo chỉ dùng được 1 lần → phải lưu cái mới ngay.
    _tokens.update({"access_token": data["access_token"], "refresh_token": data["refresh_token"]})
    TOKEN_FILE.write_text(json.dumps(_tokens))
    log.info("Đã làm mới access token Zalo")
    return True


def send_text(user_id: str, text: str, _retry: bool = True) -> None:
    r = httpx.post(
        SEND_URL,
        headers={"access_token": _tokens["access_token"], "Content-Type": "application/json"},
        json={"recipient": {"user_id": user_id}, "message": {"text": text}},
        timeout=20,
    )
    data = r.json() if r.content else {}
    err = data.get("error", 0)
    if err == -216 and _retry and _refresh_token():  # -216: access token không hợp lệ/hết hạn
        return send_text(user_id, text, _retry=False)
    if err != 0:
        log.error("Gửi tin Zalo lỗi: %s", data)


def parse_events(body: dict, is_bot_text) -> list[dict]:
    """is_bot_text(user_id, text) -> bool: nhận ra tin OA gửi đi là do bot hay do nhân viên tự nhắn."""
    name = body.get("event_name", "")
    sender = (body.get("sender") or {}).get("id", "")
    recipient = (body.get("recipient") or {}).get("id", "")
    msg = body.get("message") or {}
    text = msg.get("text") or ""
    mid = msg.get("msg_id") or f"{name}:{sender}:{body.get('timestamp')}"

    if name == "user_send_text":
        return [{"type": "message", "user_id": sender, "text": text, "mid": mid}]
    if name in {"user_send_image", "user_send_file", "user_send_sticker", "user_send_gif", "user_send_audio"}:
        return [{"type": "message", "user_id": sender, "text": "[Khách gửi hình ảnh/tệp đính kèm]", "mid": mid}]
    if name == "oa_send_text" and text and not is_bot_text(recipient, text):
        return [{"type": "staff", "user_id": recipient, "text": text, "mid": mid}]
    return []
