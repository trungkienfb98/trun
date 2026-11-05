"""Facebook Page: Messenger (tin nhắn) + Feed (bình luận trên bài của chính Page).

Chỉ dùng API chính thức của Meta, chỉ trên Page mà bạn là quản trị viên.
"""
import hashlib
import hmac
import logging

import httpx

import config

log = logging.getLogger("facebook")
CHANNEL = "facebook"
BOT_TAG = "ban-hang-ai"  # gắn vào tin bot gửi để phân biệt với tin nhân viên tự nhắn
GRAPH = f"https://graph.facebook.com/{config.FB_GRAPH_VERSION}"


def verify_signature(raw_body: bytes, header: str | None) -> bool:
    if not config.FB_APP_SECRET:
        log.warning("Chưa đặt FB_APP_SECRET — bỏ qua kiểm tra chữ ký (KHÔNG nên dùng khi chạy thật)")
        return True
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(config.FB_APP_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def _post(path: str, payload: dict) -> dict:
    r = httpx.post(f"{GRAPH}/{path}", params={"access_token": config.FB_PAGE_TOKEN}, json=payload, timeout=20)
    if r.status_code >= 400:
        log.error("Graph API %s lỗi %s: %s", path, r.status_code, r.text[:500])
    return r.json() if r.content else {}


def send_text(psid: str, text: str) -> None:
    _post(
        "me/messages",
        {
            "recipient": {"id": psid},
            "messaging_type": "RESPONSE",
            "message": {"text": text, "metadata": BOT_TAG},
        },
    )


def send_typing(psid: str) -> None:
    _post("me/messages", {"recipient": {"id": psid}, "sender_action": "typing_on"})


def reply_comment(comment_id: str, text: str) -> None:
    """Trả lời công khai dưới bình luận."""
    _post(f"{comment_id}/comments", {"message": text})


def private_reply(comment_id: str, text: str) -> None:
    """Nhắn riêng vào inbox người vừa bình luận (Private Replies — mỗi bình luận 1 lần, trong 7 ngày)."""
    _post("me/messages", {"recipient": {"comment_id": comment_id}, "message": {"text": text}})


def parse_events(body: dict) -> list[dict]:
    """Chuẩn hoá webhook thành danh sách sự kiện:
    {"type": "message"|"staff"|"comment", "user_id", "text", "mid"/"comment_id", ...}
    """
    events: list[dict] = []
    if body.get("object") != "page":
        return events
    for entry in body.get("entry", []):
        for m in entry.get("messaging", []):
            msg = m.get("message") or {}
            if not msg:
                continue
            if msg.get("is_echo"):
                # Tin do Page gửi đi. Nếu không phải bot gửi thì đó là nhân viên tự trả lời.
                if msg.get("metadata") != BOT_TAG and msg.get("text"):
                    events.append(
                        {"type": "staff", "user_id": m["recipient"]["id"], "text": msg["text"], "mid": msg.get("mid")}
                    )
                continue
            text = msg.get("text") or ""
            if not text and msg.get("attachments"):
                text = "[Khách gửi hình ảnh/tệp đính kèm]"
            events.append({"type": "message", "user_id": m["sender"]["id"], "text": text, "mid": msg.get("mid")})
        for ch in entry.get("changes", []):
            v = ch.get("value") or {}
            if ch.get("field") != "feed" or v.get("item") != "comment" or v.get("verb") != "add":
                continue
            sender = v.get("from") or {}
            if sender.get("id") == config.FB_PAGE_ID:  # bỏ qua bình luận của chính Page
                continue
            if v.get("parent_id") and v.get("parent_id") != v.get("post_id"):
                continue  # chỉ xử lý bình luận gốc, không xử lý trả lời lồng nhau
            events.append(
                {
                    "type": "comment",
                    "comment_id": v.get("comment_id"),
                    "post_id": v.get("post_id"),
                    "user_id": sender.get("id", ""),
                    "name": sender.get("name", ""),
                    "text": v.get("message", ""),
                }
            )
    return events
