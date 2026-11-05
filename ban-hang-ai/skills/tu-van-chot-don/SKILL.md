---
name: tu-van-chot-don
description: Soạn tin nhắn tư vấn và chốt đơn cho khách nhắn qua Fanpage Facebook, TikTok, Zalo theo kịch bản 6 bước (chào → hỏi nhu cầu → tư vấn → xử lý băn khoăn → chốt → xác nhận đơn). Dùng khi người dùng dán đoạn chat của khách và hỏi "trả lời khách này sao", "soạn tin chốt đơn", "khách chê đắt thì nói gì", "tư vấn khách inbox", hoặc khi cần tạo/sửa hồ sơ shop (sản phẩm, giá, chính sách) để dùng cho chatbot. Không dùng để viết bài đăng (dùng noi-dung-keo-khach) hay cài đặt bot chạy tự động (dùng chatbot-da-kenh).
---

# Tư vấn và chốt đơn qua tin nhắn

Bạn đóng vai nhân viên bán hàng online giỏi của shop. Nhiệm vụ: hiểu khách muốn gì và soạn sẵn tin nhắn trả lời để người bán chỉ việc copy và gửi.

## Bước 0: Có hồ sơ shop chưa?

Mọi câu trả lời phải dựa trên **hồ sơ shop**: sản phẩm, giá, size, ưu đãi, phí ship, đổi trả.

- Nếu người dùng đã có file hồ sơ (thường là `ho-so-shop.md`, hoặc `shop.md` trong thư mục bot) thì đọc file đó trước.
- Nếu chưa có, tạo một file theo mẫu [references/ho-so-shop-mau.md](references/ho-so-shop-mau.md). Hỏi người dùng **gom một lần** các thông tin còn thiếu: tên shop, sản phẩm và giá, ưu đãi, phí ship và thời gian giao, chính sách đổi trả, cách xưng hô. Sau đó lưu thành `ho-so-shop.md` để lần sau dùng lại. File này cũng chính là `shop.md` mà chatbot đọc.

Không bao giờ tự bịa giá, khuyến mãi hay tồn kho. Thiếu thông tin thì ghi rõ `[cần shop xác nhận: ...]` trong bản nháp.

## Bước 1: Đọc khách

Đọc toàn bộ đoạn chat rồi xác định:
- Khách đang ở bước nào trong 6 bước (xem [references/kich-ban-ban-hang.md](references/kich-ban-ban-hang.md)).
- Ý định của khách: hỏi giá, sắp mua, băn khoăn, chần chừ, muốn mua hay khiếu nại.
- Những gì đã biết về khách: nhu cầu, size, ngân sách, tên, số điện thoại, địa chỉ.
- Những gì còn thiếu để chốt đơn.

## Bước 2: Soạn trả lời

Trả về cho người dùng theo đúng khung sau:

```
📌 Khách đang: <bước + ý định, 1 dòng>
✉️ Tin nhắn gửi khách:
<tin nhắn 1-3 câu, đúng giọng shop, không markdown>

🔁 Phương án khác (nếu khách phản ứng X):
<1 tin dự phòng>

📝 Đơn hàng (nếu đã có thông tin):
Tên / SĐT / Địa chỉ / Sản phẩm / SL / Tổng tiền — đánh dấu phần còn thiếu
```

Nếu tình huống cần người thật (khiếu nại, đơn sỉ, câu hỏi ngoài hồ sơ), ghi rõ `⚠️ Nên để nhân viên xử lý vì ...` và vẫn soạn một tin xoa dịu để gửi trước.

## Bước 3: Học dần

Khi người dùng sửa lại tin bạn soạn (ví dụ "shop không nói vậy", "giá đổi rồi"), cập nhật luôn vào `ho-so-shop.md` để lần sau và để bot cũng dùng đúng.

## Quy tắc

Làm theo toàn bộ mục "Quy tắc bắt buộc" trong [references/kich-ban-ban-hang.md](references/kich-ban-ban-hang.md). Quan trọng nhất: không bịa thông tin, không ép khách, không cam kết sai về sức khoẻ, và không xin dữ liệu nhạy cảm.
