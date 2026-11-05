# Kết nối từng kênh

Giao diện của Meta và Zalo thay đổi thường xuyên. Nếu tên nút khác với hướng dẫn dưới đây, hãy tìm mục có ý nghĩa tương tự, hoặc mở tài liệu chính thức: developers.facebook.com/docs/messenger-platform và developers.zalo.me.

## Facebook Page (Messenger + bình luận)

Cần có: quyền quản trị Page và một tài khoản Meta for Developers.

1. Vào developers.facebook.com → **My Apps** → **Create App**, chọn loại **Business**.
2. Trong app, thêm sản phẩm **Messenger**. Mục **Access Tokens** → chọn Page → **Generate token**. Dán token vào `FB_PAGE_TOKEN`.
3. **App settings → Basic**: copy **App Secret** vào `FB_APP_SECRET`. Mã số Page (xem trong phần Giới thiệu của Page) điền vào `FB_PAGE_ID`.
4. Trong Messenger → **Webhooks**:
   - Callback URL: `https://<địa-chỉ-bot>/webhook/facebook`
   - Verify token: đúng giá trị `FB_VERIFY_TOKEN` trong `.env`
   - Bấm **Verify and save**, rồi đăng ký Page với các trường: `messages`, `message_echoes`, `feed`.
5. Quyền cần có: `pages_messaging`, `pages_manage_metadata`, `pages_read_engagement`, `pages_manage_engagement` (để trả lời bình luận), `pages_show_list`.
6. Khi app còn ở chế độ **Development**, bot chỉ trả lời những người có vai trò trong app. Muốn trả lời mọi khách, phải gửi **App Review** xin quyền trên và chuyển app sang **Live**. Meta yêu cầu có chính sách quyền riêng tư (privacy policy URL) và video quay màn hình bot hoạt động.

Quy định của Messenger cần nhớ:
- Bot chỉ được nhắn tự do trong **24 giờ** kể từ tin cuối của khách. Bot này chỉ trả lời khi khách nhắn, nên luôn nằm trong khung đó.
- Private Reply cho một bình luận chỉ gửi được 1 lần, trong vòng 7 ngày kể từ khi khách bình luận.

## Zalo Official Account

Cần có: một OA (nên xác thực doanh nghiệp) và tài khoản developers.zalo.me.

1. developers.zalo.me → **Tạo ứng dụng**. Lấy **App ID** điền vào `ZALO_APP_ID` và **Khoá bí mật** của ứng dụng điền vào `ZALO_APP_SECRET`.
2. Liên kết OA với ứng dụng (mục **Official Account**), rồi cấp quyền gửi và nhận tin.
3. Lấy access token và refresh token của OA bằng công cụ **API Explorer** của Zalo hoặc luồng OAuth v4. Điền vào `ZALO_ACCESS_TOKEN` và `ZALO_REFRESH_TOKEN`. Access token hết hạn sau khoảng 25 giờ; bot tự làm mới và lưu token mới vào `zalo_tokens.json`. Lưu ý: refresh token của Zalo chỉ dùng được 1 lần, nên đừng xoá file này.
4. Mục **Webhook**:
   - URL: `https://<địa-chỉ-bot>/webhook/zalo`
   - Copy **OA Secret Key** vào `ZALO_OA_SECRET` (dùng để kiểm tra chữ ký)
   - Bật các sự kiện: `user_send_text`, `user_send_image`, `user_send_file`, `user_send_sticker`, `oa_send_text`.
5. Zalo yêu cầu xác thực tên miền của webhook bằng file hoặc thẻ meta. Làm theo hướng dẫn trong trang quản lý ứng dụng.

Lưu ý: Tin Tư vấn chỉ gửi được trong khung thời gian Zalo cho phép sau khi khách tương tác. Gói OA và hạn mức tin thay đổi theo chính sách của Zalo, nên kiểm tra trang giá của Zalo OA.

## TikTok

TikTok Business Messaging API (nhắn tin trực tiếp cho tài khoản doanh nghiệp) hiện **chỉ mở cho đối tác hoặc tài khoản được TikTok duyệt** và không có ở mọi thị trường. Cách làm thực tế:

1. Kiểm tra quyền truy cập tại developers.tiktok.com và TikTok Business Center. Nếu chưa được cấp, đừng dùng công cụ giả lập để tự động nhắn: tài khoản sẽ bị khoá.
2. Trong lúc chờ, dẫn khách từ TikTok về kênh có bot: để link Messenger (`m.me/<page>`) hoặc Zalo OA ở bio, ghim bình luận, và ghi lời kêu gọi trong video kiểu "nhắn Zalo shop để được tư vấn size".
3. Khi đã được cấp API, thêm `channels/tiktok.py` theo đúng khuôn của `facebook.py` (gồm `verify_signature`, `parse_events`, `send_text`) và một route `/webhook/tiktok` trong `app.py`. Phần AI dùng lại `engine.handle_customer_message` y như các kênh khác.

## Báo đơn về Google Sheets (không bắt buộc)

1. Tạo một Google Sheet → **Tiện ích mở rộng → Apps Script**, dán đoạn sau:
   ```javascript
   function doPost(e) {
     const d = JSON.parse(e.postData.contents);
     const sh = SpreadsheetApp.getActive().getSheetByName(d.loai === "don_hang" ? "Don" : "Can_nhan_vien")
       || SpreadsheetApp.getActive().insertSheet(d.loai === "don_hang" ? "Don" : "Can_nhan_vien");
     sh.appendRow([new Date(), d.kenh, d.khach, d.ten || "", d.sdt || "", d.dia_chi || "",
                   d.san_pham || "", d.so_luong || "", d.tong_tien || "", d.ly_do || d.ghi_chu || ""]);
     return ContentService.createTextOutput("ok");
   }
   ```
2. **Triển khai → Ứng dụng web**, quyền truy cập: "Bất kỳ ai". Copy URL vào `ORDER_WEBHOOK_URL`.
