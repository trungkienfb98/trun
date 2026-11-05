"""Máy chủ webhook của chatbot bán hàng.

Chạy:  uvicorn app:app --host 0.0.0.0 --port 8000
Các đường dẫn:
  GET/POST /webhook/facebook   — Messenger + bình luận Page
  POST     /webhook/zalo       — Zalo OA
  GET      /don-hang?key=...   — xem đơn đã chốt (JSON)
  GET      /                   — kiểm tra bot còn sống
"""
import json
import logging
from collections import defaultdict, deque

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

import config
import engine
import store
from channels import facebook, zalo

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("app")
app = FastAPI(title="Bán hàng AI")

# Nhớ các tin bot vừa gửi để không nhầm là tin của nhân viên (Zalo không có metadata như Messenger).
_recent_bot_texts: dict[str, deque] = defaultdict(lambda: deque(maxlen=10))


def _send_fb(user_id: str, parts: list[str]) -> None:
    for p in parts:
        facebook.send_text(user_id, p)


def _send_zalo(user_id: str, parts: list[str]) -> None:
    for p in parts:
        _recent_bot_texts[user_id].append(p.strip())
        zalo.send_text(user_id, p)


@app.get("/")
def health() -> dict:
    return {"ok": True, "model": config.CLAUDE_MODEL, "shop_file": str(config.SHOP_FILE)}


# ---------------- Facebook ----------------
@app.get("/webhook/facebook")
def fb_verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == config.FB_VERIFY_TOKEN:
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(403, "Sai verify token")


def _process_fb(events: list[dict]) -> None:
    for ev in events:
        try:
            if ev["type"] == "staff":
                if ev.get("mid") and store.already_seen(f"fb:{ev['mid']}"):
                    continue
                engine.staff_replied(facebook.CHANNEL, ev["user_id"], ev["text"])
            elif ev["type"] == "message":
                if ev.get("mid") and store.already_seen(f"fb:{ev['mid']}"):
                    continue
                facebook.send_typing(ev["user_id"])
                parts = engine.handle_customer_message(facebook.CHANNEL, ev["user_id"], ev["text"])
                _send_fb(ev["user_id"], parts)
            elif ev["type"] == "comment" and config.FB_REPLY_COMMENTS:
                # Mỗi người chỉ được nhắn riêng 1 lần cho mỗi bài, tránh làm phiền.
                if store.already_seen(f"fbc:{ev['post_id']}:{ev['user_id']}"):
                    continue
                parts = engine.handle_customer_message(
                    "facebook_comment", ev["user_id"], f"(Khách bình luận dưới bài đăng) {ev['text']}", ev["name"]
                )
                if parts:
                    facebook.private_reply(ev["comment_id"], "\n\n".join(parts))
                    facebook.reply_comment(ev["comment_id"], config.FB_COMMENT_REPLY_TEXT)
        except Exception:  # một sự kiện lỗi không được làm hỏng các sự kiện khác
            log.exception("Lỗi xử lý sự kiện Facebook: %s", ev)


@app.post("/webhook/facebook")
async def fb_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not facebook.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(403, "Sai chữ ký")
    events = facebook.parse_events(json.loads(raw))
    background.add_task(_process_fb, events)  # trả 200 ngay, Facebook yêu cầu phản hồi nhanh
    return {"ok": True}


# ---------------- Zalo ----------------
def _is_bot_text(user_id: str, text: str) -> bool:
    return text.strip() in _recent_bot_texts[user_id]


def _process_zalo(events: list[dict]) -> None:
    for ev in events:
        try:
            if store.already_seen(f"zl:{ev['mid']}"):
                continue
            if ev["type"] == "staff":
                engine.staff_replied(zalo.CHANNEL, ev["user_id"], ev["text"])
            else:
                parts = engine.handle_customer_message(zalo.CHANNEL, ev["user_id"], ev["text"])
                _send_zalo(ev["user_id"], parts)
        except Exception:
            log.exception("Lỗi xử lý sự kiện Zalo: %s", ev)


@app.post("/webhook/zalo")
async def zalo_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not zalo.verify_signature(raw, request.headers.get("X-ZEvent-Signature")):
        raise HTTPException(403, "Sai chữ ký")
    events = zalo.parse_events(json.loads(raw), _is_bot_text)
    background.add_task(_process_zalo, events)
    return {"ok": True}


# ---------------- Quản lý ----------------
@app.get("/don-hang")
def orders(key: str = ""):
    if not config.ADMIN_KEY or key != config.ADMIN_KEY:
        raise HTTPException(403, "Cần ?key=ADMIN_KEY")
    return store.list_orders()
