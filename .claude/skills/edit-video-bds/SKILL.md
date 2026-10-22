---
name: edit-video-bds
description: Edit video talking-head bất động sản (môi giới nói trước camera) thành video TikTok/Reels dọc 9:16 theo phong cách "infographic BĐS" — tiêu đề hook có thanh màu, nền mờ khi hiện thông số, số đếm chạy (270ha, 2,4 tỷ), thẻ dự án viền đỏ, thẻ ảnh sản phẩm có nhãn "830 CĂN", nền lưới xanh, checklist chính sách, phụ đề tiếng Việt chạy theo từng từ, tiếng pop/whoosh, chuẩn âm lượng. Dùng khi người dùng gửi video và nói "edit video", "dựng video giống mẫu", "làm video BĐS", "chèn chữ/phụ đề/hiệu ứng cho video", "edit video dự án Vinhomes...", hoặc gọi /edit-video-bds.
---

# Edit video BĐS kiểu TikTok infographic

Quy trình: video gốc → (cắt khoảng lặng) → chép lời có mốc thời gian → viết `plan.json` (chữ, số, ảnh, phụ đề khớp từng từ) → render → xem khung hình kiểm lỗi → gửi file.

Mọi script nằm trong `scripts/` cạnh file này (gọi là `$SKILL`). Cần Python 3 + Pillow + numpy; ffmpeg dùng bản hệ thống, nếu không có script tự `pip install imageio-ffmpeg`.
Trên Windows gọi `py -3` hoặc `python` thay cho `python3`. Bộ cài cho máy khác: thư mục `installer/` của repo (tự cài thư viện + chép skill vào `~/.claude/skills`).

## Bước 1 — Nhận video và hỏi đủ thông tin

Xem video trước (`python3 $SKILL/scripts/common.py video.mp4` để biết kích thước/thời lượng, `preview.py` để xem khung hình). Chỉ hỏi những gì thiếu:

- **Ảnh/video dự án** để chèn (phối cảnh, mặt bằng, từng dòng sản phẩm, tiện ích). Không có thì vẫn dựng được bằng chữ + thẻ tiêu đề; **không bao giờ tự vẽ/tạo ảnh giả làm ảnh dự án thật**.
- Tên kênh/handle (watermark, CTA), có muốn nhạc nền không (người dùng gửi file nhạc, hoặc chọn nhạc trong thư viện TikTok khi đăng).
- Số liệu cần nhấn (giá, diện tích, số căn, chính sách) nếu lời nói chưa rõ.

Nếu môi trường có truy cập web và người dùng muốn lấy ảnh "trên các nền tảng": chỉ lấy từ nguồn chính thức (website/fanpage chủ đầu tư) hoặc nguồn người dùng chỉ định, ghi lại nguồn. Mạng bị chặn thì nói rõ host nào bị chặn và xin người dùng tải ảnh lên.

## Bước 2 — Cắt khoảng lặng (tuỳ chọn, giống mẫu)

```bash
python3 $SKILL/scripts/jumpcut.py input.mp4 cut.mp4 --min-silence 0.35
```
Luôn chép lời **trên file đã cắt** để mốc thời gian khớp.

## Bước 3 — Chép lời có mốc thời gian

```bash
python3 $SKILL/scripts/transcribe.py cut.mp4 words.json
```
Model tiếng Việt offline (~260 MB, tải 1 lần từ GitHub Releases vào `~/.cache/edit-video-bds`). Kết quả viết HOA, không dấu câu, hay sai tên riêng ("VINH HOM" → Vinhomes, "VIOM KINH BẮC" → Vinhomes Kinh Bắc, "HAI TRĂM BẢY MƯƠI" → 270). Sửa khi viết plan và **đưa lời thoại đã sửa cho người dùng xác nhận** nếu có chỗ không chắc (tên người, số liệu).

Nếu không tải được model: xin người dùng gõ lời thoại, rồi ước lượng mốc thời gian bằng cách chia đều các từ trong các đoạn có tiếng (dùng `silencedetect` của ffmpeg để tìm đoạn có tiếng).

## Bước 4 — Viết plan.json

Mẫu đầy đủ: `examples/plan-example.json` (hook 10s "Tại sao Vinhomes chọn Bắc Ninh"). Toạ độ theo khung 1080×1920, `x`/`y` là **tâm** phần tử. Thời gian tính bằng giây.

| Khoá gốc | Ý nghĩa |
|---|---|
| `video` | đường dẫn video (tương đối với plan) |
| `output` | `{"width":1080,"height":1920,"fps":30}` |
| `crop_x` | 0..1, dịch khung cắt ngang khi video gốc rộng hơn 9:16 (0.5 = giữa) |
| `grade` | chỉnh nhẹ tương phản/độ nét (mặc định true) |
| `blur` | `[[start,end],...]` làm mờ nền + tối nhẹ (lúc hiện thông số/liệt kê) |
| `grid` | `[[start,end],...]` thay nền bằng lưới đen→xanh toàn màn hình (màn thông số) |
| `sfx` | tiếng pop ở mỗi phần tử xuất hiện + whoosh khi vào blur/grid (mặc định true) |
| `music` | `{"path":"nhac.mp3","volume":0.12}` lặp nhạc, nhỏ dưới giọng, fade cuối |
| `caption_style` | `{"y":1330,"size":62,"highlight":"yellow"}` |
| `captions` | `[{"start","end","words":[["Tại",0.0],["sao",0.68],...]}]` — mỗi cụm 3–6 từ, ≤2 dòng; từ đã nói đổi màu highlight |
| `elements` | danh sách phần tử, vẽ theo thứ tự (sau đè trước) |

Phần tử chung: `type`, `start`, `end` (bỏ trống = đến hết), `x`, `y`, `scale`, `anim` (`pop` mặc định | `blur` | `slide` | `none`), `anim_dur`, `sfx` (false để tắt tiếng pop).

| `type` | Khoá riêng |
|---|---|
| `title` | `line1`, `line2`, `line2_at` (lúc thanh màu quét ra), `y`, `size`, `color1`, `color2`, `bar` |
| `text` | `text`, `font` (`heading` Oswald \| `body` Be Vietnam Pro \| `script` chữ viết tay), `size`, `color`, `stroke` |
| `counter` | `from`, `to`, `duration`, `decimals`, `prefix`, `suffix`, `font` (mặc định script), `size`, `color` — số kiểu Việt "2,4" / "1.210" |
| `card` | `small` (dòng nhỏ giãn chữ), `big`, `location` (ghim đỏ + chữ vàng), `border` |
| `image` | `path`, `width`, `height` (cắt vừa khung), `label` (chữ to ở đáy ảnh, vd "830 CĂN"), `label_size`, `border` |
| `badge` | `text`, `icon` (`clock` \| `check` \| `none`), `color`, `text_color`, `size` |
| `checklist` | `items:[{"text","at"}]`, `x` (mép trái), `y` (dòng đầu), `gap`, `size` |
| `arrow` | mũi tên chỉ xuống: `length`, `color` |

Màu: `white yellow cyan red teal green black navy` hoặc `"#RRGGBB"`.

### Quy tắc dựng (học từ video mẫu)

- **Khớp lời:** mỗi phần tử xuất hiện đúng lúc người nói nhắc tới (lấy `start` từ words.json, sớm hơn ~0.05s).
- **Bảng màu cố định:** trắng = nhãn, cyan chữ viết tay = con số diện tích/quy mô, vàng = thông tin phụ/nhấn, đỏ = phép tính & khan hiếm ("Duy nhất"), xanh lá = xác nhận ✓.
- **Hook 0–3s:** `title` 2 dòng là câu hỏi/lợi ích chính. Thông số liệt kê → `blur` + chữ/ảnh pop lần lượt. Nhiều thông số liên tiếp → `grid` + ảnh sản phẩm trên cùng, chữ hiện từng dòng (`anim: blur`), ✓ bật lần lượt.
- **Ẩn phụ đề** trong các đoạn blur/grid (không tạo caption cho khoảng đó) để màn hình không rối.
- **Vùng an toàn:** không đè mặt người nói; TikTok che ~380px dưới cùng và ~140px bên phải — phụ đề quanh y≈1250–1400, nội dung quan trọng x trong 80–940.
- **Thẻ/huy hiệu chồng nhau:** card ở y≈270 (scale 0.88), badge dưới nó y≈505 (scale 0.8). Hai dòng tiêu đề cách nhau `size*1.62` (đã tự tính).
- Kết bằng CTA (comment/inbox) — dùng `badge` hoặc `checklist`.

## Bước 5 — Render và kiểm tra

```bash
python3 $SKILL/scripts/render.py plan.json out.mp4
python3 $SKILL/scripts/preview.py out.mp4 sheet.jpg            # 2 khung/giây
python3 $SKILL/scripts/preview.py out.mp4 check.jpg 2.3 4.7 8.6  # các thời điểm cần soi
```
Xem ảnh preview và soi kỹ: dấu tiếng Việt bị che/cắt (đặc biệt dấu nặng dưới chữ hoa), chữ đè nhau, che mặt, phụ đề rớt 1 từ xuống dòng (tách cụm lại), số đếm chạy đúng. Sửa plan → render lại. Tốc độ ~3s render cho 1s video 1080p.

## Bước 6 — Giao file

Gửi `out.mp4` cho người dùng, kèm: lời thoại đã sửa, các chỗ cần họ xác nhận, và danh sách tư liệu còn thiếu (ảnh, nhạc, handle) để ra bản tốt hơn.

## Giấy phép font

Oswald, Be Vietnam Pro, Dancing Script — SIL Open Font License (`assets/fonts/OFL-*.txt`).
