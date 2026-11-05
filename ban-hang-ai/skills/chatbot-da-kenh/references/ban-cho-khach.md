# Gợi ý khi bán dịch vụ chatbot cho shop khác

## Gói dịch vụ mẫu

| Gói | Gồm | Ghi chú chi phí của bạn |
|---|---|---|
| Cơ bản | Bot Messenger + soạn hồ sơ shop + 1 lần chỉnh kịch bản | Tiền máy chủ + tiền API Claude theo số tin |
| Chuẩn | Thêm Zalo OA + tự trả lời bình luận + đơn về Google Sheets | Như trên |
| Trọn gói | Thêm 30 bài đăng/tháng (skill `noi-dung-keo-khach`) + hẹn giờ đăng lên Page (skill `dang-bai-hen-gio`) | Thêm thời gian soạn nội dung |

Chi phí API tính theo token. Hãy chạy thử khoảng 50 cuộc chat thật bằng `chat_thu.py`, rồi xem mục Usage trên console.anthropic.com để biết giá vốn trung bình mỗi cuộc chat, sau đó mới báo giá cho khách. Đừng báo giá "không giới hạn tin" khi chưa đo.

## Những điều cần nói rõ với khách

- Bot chạy trên **API chính thức**. Khách phải tự sở hữu Page, OA và tài khoản developer, và phải qua App Review của Meta để bot trả lời mọi người.
- Bot **không** nhắn tin hàng loạt, **không** đăng hay bình luận vào nhóm. Đây là điểm bán hàng: Page an toàn, không bị khoá.
- Bot có thể trả lời sai. Shop phải kiểm tra hồ sơ sản phẩm và theo dõi các cuộc chat bị chuyển nhân viên trong tuần đầu.
- Dữ liệu khách (tên, số điện thoại, địa chỉ) là dữ liệu cá nhân. Theo Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân, shop cần có chính sách quyền riêng tư và chỉ dùng dữ liệu để giao hàng và chăm sóc khách. Mỗi shop dùng một bản cài riêng để dữ liệu không lẫn vào nhau.

## Quy trình bàn giao cho một shop

1. Phỏng vấn chủ shop và điền `shop.md` (dùng skill `tu-van-chot-don`, bước 0).
2. Chạy `chat_thu.py` cùng chủ shop, sửa đến khi họ hài lòng.
3. Triển khai bot, kết nối kênh, gửi App Review.
4. Tuần đầu: mỗi ngày đọc lại các cuộc chat bị chuyển nhân viên, bổ sung thông tin còn thiếu vào `shop.md`.
