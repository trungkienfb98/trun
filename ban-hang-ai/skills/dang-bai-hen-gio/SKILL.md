---
name: dang-bai-hen-gio
description: Lên lịch và hẹn giờ đăng bài tự động lên Fanpage Facebook của chính mình qua Graph API chính thức (script dang_bai.py đọc file CSV), kèm hướng dẫn hẹn giờ trên Zalo OA và TikTok bằng công cụ chính chủ. Dùng khi người dùng nói "hẹn giờ đăng bài", "lên lịch đăng page", "đăng bài tự động lên fanpage", "lịch đăng 30 ngày", "auto post page". KHÔNG dùng để đăng vào nhóm hay đăng bằng nick cá nhân: việc đó vi phạm điều khoản nền tảng, nên hướng sang skill noi-dung-keo-khach.
---

# Hẹn giờ đăng bài lên kênh của chính bạn

## Giới hạn: chỉ kênh mình sở hữu

| Kênh | Cách tự động hợp lệ |
|---|---|
| Fanpage Facebook | Script [scripts/dang_bai.py](scripts/dang_bai.py) gọi Graph API, dùng tính năng hẹn giờ có sẵn của Facebook |
| Zalo OA | Hẹn giờ trong trang quản lý OA (oa.zalo.me), mục bài viết / broadcast, theo hạn mức gói OA |
| TikTok | Hẹn giờ trong TikTok Studio (bản web). Content Posting API chỉ dành cho app đã được TikTok duyệt |
| **Nhóm Facebook/Zalo, nick cá nhân** | **Không tự động hoá.** Meta đã gỡ API đăng vào nhóm từ năm 2024. Tool giả lập trình duyệt sẽ làm khoá nick. Hãy soạn nội dung bằng `noi-dung-keo-khach` rồi đăng tay |

Nếu người dùng xin đăng tự động vào nhóm, giải thích ngắn lý do trên rồi đề nghị cách thay thế. Không viết code giả lập trình duyệt, không đổi IP hay xoay nick để lách kiểm duyệt.

## Quy trình

1. **Có nội dung.** Nếu chưa có bài, dùng skill `noi-dung-keo-khach` (hoặc `social-content`) để soạn trước. Mỗi bài phải khác nhau thật sự, không chỉ đổi vài chữ.
2. **Lập lịch.** Tạo file CSV theo mẫu [scripts/lich_dang_mau.csv](scripts/lich_dang_mau.csv) với các cột `thoi_gian, noi_dung, anh_url, link`.
   - Giờ Việt Nam, dạng `2026-11-20 19:30`, từ 15 phút đến 29 ngày tính từ lúc chạy.
   - Gợi ý nhịp đăng: 1-2 bài mỗi ngày, mỗi bài cách nhau ít nhất 2 giờ. Khung giờ hay có tương tác là 11h-13h và 19h-22h; xem Insights của Page để chọn giờ đúng với khách của shop.
   - Tỷ lệ gợi ý: khoảng 70% bài mang lại giá trị (mẹo, kiến thức, câu chuyện, feedback), 30% bài bán hàng.
   - `anh_url` phải là link ảnh công khai (ví dụ ảnh đã tải lên một host ảnh). Script không tải ảnh từ máy lên.
3. **Chạy thử** (không đăng gì):
   ```bash
   pip install httpx
   python scripts/dang_bai.py lich_dang.csv
   ```
   Đọc cảnh báo và sửa nếu có.
4. **Gửi lịch thật.** Cần `FB_PAGE_ID` và `FB_PAGE_TOKEN` (Page token có quyền `pages_manage_posts`, `pages_read_engagement`) trong biến môi trường hoặc file `.env`. Có thể dùng chung `.env` của bot `chatbot-da-kenh`, nhưng token phải có thêm quyền đăng bài.
   ```bash
   python scripts/dang_bai.py lich_dang.csv --that
   ```
   Kiểm tra lại trong Meta Business Suite → **Lịch**, có thể sửa hoặc xoá từng bài ở đó.

## Kết hợp với chatbot

Bài đăng trên Page nên kêu gọi khách **bình luận** hoặc **inbox** (ví dụ "comment SIZE để shop tư vấn"). Khi bot `chatbot-da-kenh` bật `FB_REPLY_COMMENTS=1`, mỗi bình luận sẽ được nhắn riêng vào inbox và bot tư vấn, chốt đơn tiếp. Đây là cách "dồn khách về inbox" hợp lệ và hiệu quả nhất.
