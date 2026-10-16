---
name: auto-edit-video-tiktok
description: Tự động dựng video nói chuyện (talking-head) kiểu TikTok/Reels: cắt khoảng lặng, tiêu đề chữ phát sáng theo lời thoại, zoom nhảy, ảnh trám, nhạc nền và hiệu ứng âm thanh.
---

# Tự động edit video kiểu TikTok/Reels

Dùng khi người dùng gửi một video quay người nói (dọc 9:16) kèm lời thoại và muốn: chữ hiệu ứng phát sáng (chữ viết tay + chữ đậm nhấn từ khóa), cắt khoảng lặng, zoom nhảy theo câu, ảnh trám (B-roll), nhạc nền, hiệu ứng âm thanh.

Toàn bộ chạy offline bằng `scripts/autoedit.py` (đi kèm skill): ffmpeg + python3 + numpy + scipy + pillow. Không cần mạng: nhạc nền và SFX được tổng hợp bằng code, ảnh trám là đồ họa neon vẽ bằng code (hoặc ảnh thật nếu người dùng gửi).

## Quy trình

1. **Đầu vào.** Cần file video và **toàn bộ lời thoại, mỗi câu một dòng**. Nếu thiếu lời thoại, hỏi người dùng (không đoán nội dung; mô hình không nghe được âm thanh). Nếu họ có nhạc riêng hoặc ảnh/clip B-roll, nhận luôn.
2. **Tạo thư mục làm việc**, sao chép `scripts/autoedit.py` của skill vào đó. Mẫu plan đầy đủ: `examples/plan.json`.
3. **Viết `plan.json`** (xem mẫu). Trước hết chỉ cần `input`, `output`, `lines`.
4. Chạy `python3 autoedit.py prep plan.json` (tạo bản 1080×1920 trung gian + voice.wav; video 4K mất ~2 phút).
5. Chạy `python3 autoedit.py align plan.json` → in thời gian từng câu (`work/lines.json`). Thuật toán khớp số âm tiết với các quãng ngắt, nên kiểm tra hợp lý: câu ngắn phải ngắn, tốc độ ~4–6 âm tiết/giây. Câu nào sai thì sửa bằng `"line_times": {"5": [13.9, 16.9]}` rồi chạy lại.
6. Chạy `python3 autoedit.py cuts plan.json` → các đoạn giữ lại sau khi cắt khoảng lặng (quãng ngắt ≥ `min_pause`, mặc định 0.24s). Đoạn thừa/nói vấp cần bỏ thêm: `"extra_cuts": [[s, e], ...]` (thời gian gốc).
7. **Thiết kế tiêu đề** (`titles`) và **ảnh trám** (`broll`), `punch`, `sfx_events` theo nguyên tắc bên dưới.
8. `python3 autoedit.py preview plan.json` → xem `work/preview.jpg` bằng Read. Sửa chữ tràn khung, đè lên nhau, che mặt. Lặp lại tới khi ổn.
9. `python3 autoedit.py render plan.json` (khoảng 5–6 phút cho 1 phút video; chạy nền với nohup nếu dài) → tự nén dưới `max_mb` (mặc định 29 MB, để gửi được qua SendUserFile).
10. Kiểm tra: `python3 autoedit.py probe plan.json 1 8.5 20` → `work/probe.jpg` (thời gian theo video mới). Rồi gửi file bằng SendUserFile.
11. Báo kết quả ngắn gọn, nói rõ giới hạn: không nghe thử được âm thanh (chỉ đo mức), thời gian câu ước lượng theo quãng ngắt, nhạc/ảnh trám là tự tạo. Mời người dùng chỉ giây cần chỉnh.

## Nguyên tắc thiết kế tiêu đề

- Mỗi câu thoại → 1 tiêu đề (câu dài > ~6 giây thì tách 2–3 tiêu đề bằng `"part": [0, 0.36]`). Đây là **tiêu đề nhấn từ khóa**, không phải phụ đề chép đủ chữ.
- Cấu trúc 3 lớp như mẫu template: chữ viết tay nhỏ dẫn câu (lệch trái, phía trên) → **từ khóa in đậm phát sáng** (giữa) → chữ viết tay kết (lệch phải, phía dưới). Từ khóa ≤ 3–4 từ.
- Đổi màu xoay vòng giữa các câu: `orange, blue, cyan, gold, pink, purple, red, green, mint, magenta, rainbow, white`. Từ khóa cảm xúc/sang trọng dùng `serif` + `gold`/`pink`; từ khóa mạnh dùng `black`; còn lại `bold`.
- Đổi hiệu ứng xuất hiện: `blur` (mờ → rõ), `pop` (bật nảy, có tiếng pop), `rise` (trượt lên), `swing` (xoay vào), `spread` (giãn chữ). Câu cực ngắn (< 1s) dùng `pop`.
- Vị trí: `title_y` (tỉ lệ chiều cao, mặc định 0.8) phải nằm ở vùng không có mặt người – thường là vùng áo phía dưới. Xem một khung hình trước khi chọn. Tiêu đề riêng có thể đặt `"y": 0.16`.
- Tọa độ lớp `x`, `y` tính theo pixel trên khung 1080 rộng, so với tâm tiêu đề; chữ viết tay thường ở `x` ±150–220, `y` ±100.
- Nhãn (`pill`) cho câu kêu gọi hành động: `{"type":"pill","text":"TỰ ĐỘNG","y":120,"box":"#f0c25a","ink":"#3b2700","radius":40}`.
- Chữ tự thu nhỏ nếu quá rộng (chữ đậm ≤ 980px, viết tay ≤ 760px).

## Ảnh trám, zoom, âm thanh

- `broll`: dùng cho câu liệt kê/ví dụ (ngắn 1–3s). Loại có sẵn: `shop, mic, review, house, car, phone, ai, color, cut, clock, chart, money, heart, check, comment`. Ảnh thật: `{"line": 4, "kind": "image", "image": "/đường/dẫn/anh.jpg"}` (tự Ken Burns + làm tối nửa dưới cho chữ). Không phủ ảnh trám lên câu mở đầu (hook) và câu kêu gọi cuối – giữ mặt người nói.
- Zoom nhảy tự động theo mỗi tiêu đề (`zoom_levels`, mặc định [1.0, 1.14, 1.06, 1.2]); `face` = [x, y] tỉ lệ vị trí mặt để zoom vào. `punch`: zoom mạnh + tiếng "bùm" cho câu nhấn (vd "zoom này").
- Nhạc: mặc định tự tổng hợp (110 BPM, Am–F–C–G, tự nhỏ xuống khi có giọng). Nhạc riêng: `"music_file": "..."`. Âm lượng: `music_volume` (1.0), `sfx_volume` (1.0). Tắt: `"music": false`, `"sfx": false`.
- SFX tự động: whoosh khi tiêu đề hiện, pop cho `pop`, lướt khi vào ảnh trám. Thêm theo câu: `"sfx_events": [{"at_line":17,"type":"riser"},{"at_line":17,"type":"impact","offset":0.25},{"at_line":18,"type":"ding","offset":0.3}]` (riser trước "Và bây giờ…", ding ở lời kêu gọi).

## plan.json mẫu

```json
{
 "input": "/mnt/user-data/uploads/clip.mp4",
 "output": "video-da-edit.mp4",
 "lines": ["Bạn có tin rằng chỉ cần một công cụ AI ...", "Từ video bán hàng này,", "podcast này,", "..."],
 "title_y": 0.8,
 "face": [0.47, 0.42],
 "titles": [
  {"line": 0, "part": [0, 0.36], "anim": "swing", "layers": [
    {"type": "script", "text": "Bạn có tin rằng chỉ cần", "x": -90, "y": -110, "size": 88},
    {"type": "bold", "text": "1 CÔNG CỤ AI", "color": "blue", "size": 150},
    {"type": "script", "text": "duy nhất", "x": 200, "y": 105}]},
  {"line": 1, "anim": "pop", "layers": [
    {"type": "script", "text": "Từ video", "x": -190, "y": -95, "size": 104},
    {"type": "bold", "text": "BÁN HÀNG", "y": 10, "color": "orange", "size": 170}]},
  {"line": 2, "anim": "pop", "layers": [{"type": "black", "text": "PODCAST", "color": "purple", "size": 180}]}
 ],
 "broll": [{"line": 1, "kind": "shop"}, {"line": 2, "kind": "mic"}],
 "punch": [{"line": 13}],
 "sfx_events": [{"at_line": 17, "type": "riser"}, {"at_line": 18, "type": "ding", "offset": 0.3}],
 "max_mb": 29
}
```

Thay cho `line`, có thể dùng `"start"`/`"end"` (giây, thời gian gốc); `"line_to"` để kéo một mục qua nhiều câu.

## Lưu ý kỹ thuật

- Font: tự tìm Great Vibes/Oswald/Inter/Lora nếu có, nếu không dùng TeX Gyre Chorus (viết tay), TeX Gyre Heros Cn (đậm cô đặc), Inter Black, Lora – đều có dấu tiếng Việt. Kiểm tra bằng fontTools nếu đổi font.
- Video khác 9:16 sẽ bị scale + crop giữa thành 1080×1920.
- Video có nhạc nền sẵn: tách quãng ngắt kém hơn; tăng `silence_db` (vd -25) hoặc dùng `"cut_silence": false` và `line_times` thủ công.
- File > 30 MB không gửi được qua SendUserFile: giữ `max_mb` ≤ 29.
