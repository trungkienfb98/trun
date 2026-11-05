"""Lưu lịch sử chat, trạng thái chuyển người thật và đơn hàng vào SQLite."""
import json
import sqlite3
import threading
import time

import config

_lock = threading.Lock()
_conn = sqlite3.connect(config.DB_FILE, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT, user_id TEXT, role TEXT, text TEXT, ts REAL
    );
    CREATE INDEX IF NOT EXISTS idx_msg_user ON messages(channel, user_id, id);
    CREATE TABLE IF NOT EXISTS customers (
        channel TEXT, user_id TEXT, paused_until REAL DEFAULT 0, order_json TEXT,
        PRIMARY KEY (channel, user_id)
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT, user_id TEXT, order_json TEXT, ts REAL
    );
    CREATE TABLE IF NOT EXISTS seen_events (key TEXT PRIMARY KEY, ts REAL);
    """
)
_conn.commit()


def _exec(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    with _lock:
        cur = _conn.execute(sql, params)
        _conn.commit()
        return cur.fetchall()


def already_seen(key: str) -> bool:
    """Chống xử lý trùng khi Facebook/Zalo gửi lại cùng một sự kiện."""
    try:
        _exec("INSERT INTO seen_events(key, ts) VALUES (?, ?)", (key, time.time()))
        return False
    except sqlite3.IntegrityError:
        return True


def add_message(channel: str, user_id: str, role: str, text: str) -> None:
    _exec(
        "INSERT INTO messages(channel, user_id, role, text, ts) VALUES (?,?,?,?,?)",
        (channel, user_id, role, text, time.time()),
    )


def history(channel: str, user_id: str, limit: int) -> list[dict]:
    rows = _exec(
        "SELECT role, text FROM messages WHERE channel=? AND user_id=? ORDER BY id DESC LIMIT ?",
        (channel, user_id, limit),
    )
    return [{"role": r["role"], "text": r["text"]} for r in reversed(rows)]


def _ensure_customer(channel: str, user_id: str) -> None:
    _exec("INSERT OR IGNORE INTO customers(channel, user_id) VALUES (?, ?)", (channel, user_id))


def pause(channel: str, user_id: str, hours: float) -> None:
    _ensure_customer(channel, user_id)
    _exec(
        "UPDATE customers SET paused_until=? WHERE channel=? AND user_id=?",
        (time.time() + hours * 3600, channel, user_id),
    )


def resume(channel: str, user_id: str) -> None:
    _exec("UPDATE customers SET paused_until=0 WHERE channel=? AND user_id=?", (channel, user_id))


def is_paused(channel: str, user_id: str) -> bool:
    rows = _exec(
        "SELECT paused_until FROM customers WHERE channel=? AND user_id=?", (channel, user_id)
    )
    return bool(rows) and rows[0]["paused_until"] > time.time()


def get_draft_order(channel: str, user_id: str) -> dict:
    rows = _exec(
        "SELECT order_json FROM customers WHERE channel=? AND user_id=?", (channel, user_id)
    )
    if rows and rows[0]["order_json"]:
        return json.loads(rows[0]["order_json"])
    return {}


def save_draft_order(channel: str, user_id: str, order: dict) -> None:
    _ensure_customer(channel, user_id)
    _exec(
        "UPDATE customers SET order_json=? WHERE channel=? AND user_id=?",
        (json.dumps(order, ensure_ascii=False), channel, user_id),
    )


def save_order(channel: str, user_id: str, order: dict) -> int:
    _exec(
        "INSERT INTO orders(channel, user_id, order_json, ts) VALUES (?,?,?,?)",
        (channel, user_id, json.dumps(order, ensure_ascii=False), time.time()),
    )
    save_draft_order(channel, user_id, {})
    return _exec("SELECT last_insert_rowid() AS id")[0]["id"]


def list_orders(limit: int = 200) -> list[dict]:
    rows = _exec("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
    return [
        {
            "id": r["id"],
            "kenh": r["channel"],
            "khach": r["user_id"],
            "thoi_gian": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["ts"])),
            **json.loads(r["order_json"]),
        }
        for r in rows
    ]
