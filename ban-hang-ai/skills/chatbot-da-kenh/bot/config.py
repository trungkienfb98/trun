"""Đọc cấu hình từ biến môi trường (file .env)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    """Đọc file .env đơn giản (KEY=VALUE), không cần thêm thư viện."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(BASE_DIR / ".env")


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def path_env(name: str, default: str) -> Path:
    """Đường dẫn tương đối được tính từ thư mục bot, không phụ thuộc chỗ chạy lệnh."""
    p = Path(env(name, default))
    return p if p.is_absolute() else BASE_DIR / p


# --- AI ---
CLAUDE_MODEL = env("BOT_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = env("BOT_EFFORT", "low")  # low | medium | high
SHOP_FILE = path_env("SHOP_FILE", "shop.md")
PLAYBOOK_FILE = BASE_DIR / "kich-ban-ban-hang.md"
HISTORY_TURNS = int(env("HISTORY_TURNS", "20"))  # số tin gần nhất gửi cho AI

# --- Facebook Page (Messenger + bình luận) ---
FB_GRAPH_VERSION = env("FB_GRAPH_VERSION", "v23.0")
FB_PAGE_ID = env("FB_PAGE_ID")
FB_PAGE_TOKEN = env("FB_PAGE_TOKEN")
FB_APP_SECRET = env("FB_APP_SECRET")
FB_VERIFY_TOKEN = env("FB_VERIFY_TOKEN", "doi-chuoi-nay-di")
FB_REPLY_COMMENTS = env("FB_REPLY_COMMENTS", "1") == "1"
FB_COMMENT_REPLY_TEXT = env(
    "FB_COMMENT_REPLY_TEXT",
    "Dạ shop đã nhắn tin tư vấn chi tiết cho mình rồi ạ, mình check inbox giúp shop nhé ❤️",
)

# --- Zalo Official Account ---
ZALO_APP_ID = env("ZALO_APP_ID")
ZALO_OA_SECRET = env("ZALO_OA_SECRET")  # "OA Secret Key" trong trang quản lý webhook
ZALO_ACCESS_TOKEN = env("ZALO_ACCESS_TOKEN")
ZALO_REFRESH_TOKEN = env("ZALO_REFRESH_TOKEN")
ZALO_APP_SECRET = env("ZALO_APP_SECRET")  # "Khoá bí mật" của ứng dụng, dùng để làm mới token

# --- Vận hành ---
HANDOFF_HOURS = float(env("HANDOFF_HOURS", "12"))  # bot im lặng bao lâu sau khi chuyển người thật
ORDER_WEBHOOK_URL = env("ORDER_WEBHOOK_URL")  # ví dụ Google Apps Script để ghi đơn vào Google Sheets
DB_FILE = path_env("DB_FILE", "data.sqlite3")
ADMIN_KEY = env("ADMIN_KEY")  # bảo vệ trang /don-hang
