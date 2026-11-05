---
name: chatbot-da-kenh
description: Cài đặt và vận hành chatbot AI tự tư vấn, chốt đơn cho Fanpage Facebook (Messenger + tự trả lời bình luận trên bài của Page) và Zalo OA, dùng Claude và API chính thức của từng nền tảng. Bot hiểu nhu cầu khách, tư vấn theo hồ sơ shop, tự ghi đơn, chuyển nhân viên khi cần. Dùng khi người dùng nói "làm chatbot cho page", "bot tự trả lời inbox", "bot chốt đơn Zalo", "tự động trả lời bình luận page", "cài bot bán hàng", hoặc cần sửa, chạy thử, triển khai bot trong thư mục bot/ của skill này. TikTok chỉ hỗ trợ khi tài khoản được TikTok cấp quyền Business Messaging API.
---

# Chatbot bán hàng đa kênh

Code bot nằm trong [bot/](bot/). Đây là một máy chủ webhook viết bằng Python (FastAPI).

| File | Vai trò |
|---|---|
| `app.py` | Nhận webhook Facebook/Zalo, trang xem đơn `/don-hang` |
| `engine.py` | Luồng chung: lưu tin, hỏi AI, gộp thông tin đơn, chuyển người thật |
| `brain.py` | Gọi Claude với kịch bản và hồ sơ shop, nhận JSON gồm câu trả lời và đơn hàng |
| `channels/facebook.py`, `channels/zalo.py` | Kiểm tra chữ ký, đọc sự kiện, gửi tin |
| `shop.md` | **Hồ sơ shop**: chủ shop chỉ cần sửa file này |
| `kich-ban-ban-hang.md` | Kịch bản 6 bước (bản sao của skill `tu-van-chot-don`) |
| `chat_thu.py` | Chat thử ngay trên máy, không cần Facebook hay Zalo |

## Bot làm được gì

- Trả lời tin nhắn Messenger và Zalo OA 24/7 theo kịch bản tư vấn, chốt đơn.
- Tự gom thông tin tên, số điện thoại, địa chỉ, sản phẩm; khi khách xác nhận thì lưu đơn và báo về webhook (Google Sheets, n8n...).
- Có bình luận trên **bài của chính Page** thì nhắn riêng vào inbox người bình luận (Private Reply) và trả lời công khai "shop đã inbox". Mỗi người chỉ được nhắn 1 lần cho mỗi bài.
- Chuyển cho nhân viên khi khách đòi gặp người, khiếu nại, hoặc hỏi điều không có trong hồ sơ. Khi đó bot im lặng với khách đó `HANDOFF_HOURS` giờ.
- Nhân viên tự nhắn cho khách thì bot cũng tự dừng với khách đó. Gõ `#bot` trong cuộc chat để bật lại.

**Bot không làm và không được sửa để làm:** nhắn tin hàng loạt cho người chưa nhắn shop, đăng hoặc bình luận vào nhóm, tự động hoá tài khoản cá nhân. Những việc đó vi phạm điều khoản của Meta, Zalo và TikTok, và rất dễ làm khoá Page. Nếu người dùng yêu cầu, hãy giải thích lý do và đề xuất skill `noi-dung-keo-khach` hoặc `dang-bai-hen-gio`.

## Quy trình cài cho một shop

1. **Hồ sơ shop.** Tạo `bot/shop.md` theo mẫu có sẵn. Nếu người dùng đã có `ho-so-shop.md` từ skill `tu-van-chot-don` thì copy sang. Điền đủ giá, ưu đãi, ship, đổi trả: bot chỉ nói những gì có trong file này.
2. **Chạy thử trên máy:**
   ```bash
   cd bot && pip install -r requirements.txt && cp .env.example .env
   # điền ANTHROPIC_API_KEY vào .env
   python chat_thu.py
   ```
   Thử các tình huống: hỏi giá, chê đắt, hẹn suy nghĩ, chốt đơn, đòi gặp nhân viên, hỏi điều không có trong hồ sơ. Thấy chỗ nào sai thì sửa `shop.md` hoặc `kich-ban-ban-hang.md`.
3. **Đưa lên mạng.** Webhook cần một địa chỉ HTTPS công khai. Có thể dùng Render, Railway, Fly.io, một VPS chạy `uvicorn app:app --host 0.0.0.0 --port 8000` sau Nginx/Caddy, hoặc `cloudflared tunnel` để thử nhanh. Thư mục bot cần ổ đĩa lưu lâu dài cho `data.sqlite3` và `zalo_tokens.json`.
4. **Kết nối từng kênh** theo [references/cai-dat-kenh.md](references/cai-dat-kenh.md).
5. **Kiểm tra:** mở `https://<địa-chỉ>/` phải thấy `{"ok": true}`. Nhắn thử vào Page/OA bằng một tài khoản khác. Xem đơn tại `/don-hang?key=<ADMIN_KEY>`.

## Khi sửa code

- Giữ nguyên các lớp an toàn: kiểm tra chữ ký webhook, chống xử lý trùng sự kiện (`store.already_seen`), dừng bot khi chuyển người thật, giới hạn 1 private reply cho mỗi người mỗi bài.
- Model mặc định là `claude-opus-5-5` với effort `low`, đặt qua `BOT_MODEL` và `BOT_EFFORT` trong `.env`. Muốn đổi model thì để chủ shop quyết định.
- Hồ sơ shop và kịch bản được đưa vào system prompt có `cache_control`, nên các lượt chat sau rẻ hơn. Đừng chèn thứ hay thay đổi (giờ hiện tại, mã khách...) vào system prompt.
- Sau khi sửa, chạy lại `python chat_thu.py` để kiểm tra.

## Bán cho nhiều shop

Mỗi shop dùng **một bản cài riêng** (thư mục bot + `.env` + `shop.md` riêng). Có thể chạy nhiều bản trên cùng một VPS, mỗi bản một cổng. Như vậy dữ liệu khách của các shop không bị lẫn vào nhau. Xem gợi ý đóng gói và báo giá trong [references/ban-cho-khach.md](references/ban-cho-khach.md).
