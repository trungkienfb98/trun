# Bộ skill Bán hàng AI

Bộ skill cho Claude Code / Claude giúp shop online tư vấn, chốt đơn và kéo khách về Fanpage và Zalo, dùng **API chính thức** để Page không bị khoá.

| Skill | Làm gì |
|---|---|
| `tu-van-chot-don` | Dán đoạn chat của khách, Claude soạn sẵn tin trả lời theo kịch bản 6 bước. Tạo hồ sơ shop. |
| `chatbot-da-kenh` | Bot AI tự trả lời Messenger và Zalo OA 24/7, tự trả lời bình luận trên bài của Page, ghi đơn, chuyển nhân viên khi cần. Có code chạy được trong `skills/chatbot-da-kenh/bot/`. |
| `noi-dung-keo-khach` | Soạn hàng loạt bài đăng nhóm, bình luận mẫu và caption TikTok (khác nhau thật sự, đúng luật nhóm) để người bán tự đăng, kéo khách về Page/Zalo. |
| `dang-bai-hen-gio` | Hẹn giờ đăng bài lên Fanpage bằng Graph API từ file CSV. |

**Không có trong bộ này (cố ý):** tự đăng hoặc tự bình luận vào nhóm, nhắn tin hàng loạt, nuôi nick ảo. Các nền tảng cấm những việc này và sẽ khoá tài khoản.

## Cài đặt

Trong Claude Code:

```bash
/plugin marketplace add trungkienfb98/trun
```

```bash
/plugin install ban-hang-ai@trun-skills
```

Cách khác: copy từng thư mục trong `skills/` vào `~/.claude/skills/` (dùng cho mọi dự án) hoặc vào `.claude/skills/` của một dự án.

## Bắt đầu nhanh

1. Hỏi Claude: "tạo hồ sơ shop cho mình". Skill `tu-van-chot-don` sẽ hỏi thông tin và tạo `ho-so-shop.md`.
2. Chạy thử chatbot trên máy:
   ```bash
   cd skills/chatbot-da-kenh/bot && pip install -r requirements.txt && cp .env.example .env
   ```
   Điền `ANTHROPIC_API_KEY` vào `.env`, sửa `shop.md`, rồi chạy:
   ```bash
   python chat_thu.py
   ```
3. Kết nối Fanpage và Zalo OA theo `skills/chatbot-da-kenh/references/cai-dat-kenh.md`.
