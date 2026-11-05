---
name: noi-dung-keo-khach
description: Soạn hàng loạt bài đăng và bình luận mẫu để người bán TỰ ĐĂNG vào các nhóm Facebook/Zalo và kênh TikTok, kéo khách về Fanpage, Zalo OA, inbox. Mỗi bài viết khác nhau thật sự, đúng luật nhóm, đi theo hướng chia sẻ giá trị trước, bán hàng sau, nên không bị coi là spam. Dùng khi người dùng nói "viết bài đăng nhóm", "content seeding", "bài kéo khách về page", "mẫu comment vào nhóm", "viết 30 bài đăng nhóm", "caption TikTok kéo về Zalo". Không tự đăng hay tự bình luận: skill chỉ soạn nội dung. Không dùng cho sale page dài (dùng 16buocbanhang).
---

# Nội dung kéo khách từ nhóm về Page/Zalo

Skill này **chỉ soạn nội dung**. Người bán tự đăng bằng tài khoản thật của mình. Không viết tool tự đăng hay tự bình luận vào nhóm, không dùng nick ảo, không viết bình luận giả làm khách (seeding mạo danh). Lý do: vi phạm điều khoản Meta, Zalo, TikTok; dễ bị khoá nick, khoá Page; và đánh lừa người mua. Nếu người dùng yêu cầu những việc đó, giải thích ngắn rồi làm phần hợp lệ.

## Bước 0: Thông tin cần có

Đọc `ho-so-shop.md` hoặc `bot/shop.md` nếu có. Còn thiếu thì hỏi **gom một lần**:
- Sản phẩm hoặc dịch vụ, và khách hàng mục tiêu (ai, đang gặp vấn đề gì).
- Nơi muốn kéo khách về: link Page (`m.me/...`), Zalo OA, số Zalo, hay link TikTok.
- Danh sách nhóm sẽ đăng (tên nhóm + chủ đề nhóm + luật nhóm nếu biết, ví dụ "cấm để link", "chỉ đăng thứ 7").
- Số lượng bài cần viết, và câu chuyện hay kết quả thật của shop (feedback, số liệu) nếu có.

## Bước 1: Chọn góc bài theo nhóm

Mỗi nhóm có chủ đề riêng, và bài phải hợp với nhóm đó. Các dạng bài trong [references/mau-bai.md](references/mau-bai.md):
1. **Chia sẻ mẹo hoặc kiến thức**: không bán, CTA mềm ("ai cần bảng size chi tiết thì comment, mình gửi").
2. **Câu chuyện thật**: hành trình làm shop, một khách cụ thể (đã được khách đồng ý), một bài học.
3. **Hỏi ý kiến cộng đồng**: hỏi để tạo bình luận, ví dụ "mọi người chọn màu nào cho mùa đông?".
4. **Trước/sau, feedback thật**: chỉ dùng feedback có thật và đã che thông tin cá nhân.
5. **Ưu đãi**: chỉ đăng ở nhóm cho phép bán hàng, và ưu đãi phải có thật.

Nhóm cấm để link thì không để link trong bài. Thay vào đó dùng CTA kiểu "comment để mình inbox" hoặc "tìm Page tên X". Sau khi khách bình luận, người bán tự nhắn cho họ.

## Bước 2: Viết

Với mỗi bài, xuất theo khung:

```
### Bài <số> — Nhóm: <tên/chủ đề nhóm> — Dạng: <dạng bài>
Tiêu đề/câu mở: ...
Nội dung: ... (150-300 chữ, xuống dòng ngắn, tối đa 3 emoji)
CTA: ...
Gợi ý ảnh: ...
Giờ đăng gợi ý: ...
```

Quy tắc chống bị coi là spam:
- Mỗi bài có **ý chính, câu mở và cấu trúc khác nhau**. Không chỉ thay từ đồng nghĩa trong cùng một bài.
- Không đăng cùng một bài vào nhiều nhóm trong cùng một ngày. Đưa ra lịch xoay vòng để mỗi nhóm nhận một bài khác.
- Không viết hoa toàn bộ, không lặp "inbox ngay" nhiều lần, không hứa hẹn quá đà.
- Không bịa feedback, số liệu, chứng nhận hay "chỉ còn 3 suất" nếu không có thật.

## Bước 3: Bình luận mẫu (người bán tự dùng)

Soạn 10-20 câu bình luận để người bán **tự gõ** khi thấy bài phù hợp trong nhóm (người hỏi mua, xin review). Yêu cầu:
- Trả lời đúng câu hỏi của người đăng trước, giúp thật sự, rồi mới nhắc đến shop nếu hợp lý. Ví dụ: "Cao 1m6 nặng 55kg thì mặc M là vừa nha bạn. Bên mình có bảng size chi tiết, cần thì mình gửi."
- Ghi rõ dùng trong tình huống nào.
- Không viết bình luận đóng vai khách đã mua.

## Bước 4: TikTok

Với TikTok, viết caption kèm hook 3 giây đầu và CTA về Zalo/Messenger (link để ở bio). Có thể kết hợp các skill `viral-hook-writer` và `auto-edit-video-tiktok` nếu có.

## Bước 5: Giao cho bước tiếp theo

- Bài cho **Fanpage** của shop: xuất thêm file CSV đúng khuôn của skill `dang-bai-hen-gio` (`thoi_gian, noi_dung, anh_url, link`) để hẹn giờ đăng tự động.
- Bài cho **nhóm**: xuất bảng lịch đăng tay (ngày, nhóm, bài số mấy) để người bán làm theo.
