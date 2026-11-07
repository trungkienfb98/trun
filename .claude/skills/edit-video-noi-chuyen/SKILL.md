---
name: edit-video-noi-chuyen
description: Edit video dọc "nói chuyện vào camera" (review đơn hàng / tuyển dụng / tư vấn) theo phong cách mẫu "Review Yamanashi" – cắt khoảng lặng, phụ đề hộp vàng bo tròn chữ đen, hook 3 giây đầu, CTA cuối video, chuẩn hoá âm lượng cho TikTok/Reels. Dùng khi người dùng nói "edit video", "cắt video nói chuyện", "làm phụ đề vàng", "edit giống video review Yamanashi", "edit video tuyển dụng", "làm video talking head".
---

# Edit video "nói chuyện vào camera" – phong cách Review Yamanashi

Skill này đóng gói cách edit của video mẫu `Revie yamanashi cuoi.mp4`
(65s, 1080x1920, 30fps): một người nói thẳng vào camera, cắt sát khoảng lặng,
phụ đề hộp vàng. Có kèm script tự động (`scripts/edit_video.py`) và
công thức làm tay trong CapCut cho người không dùng dòng lệnh.

## 1. Phong cách mẫu (đã đo từ video gốc)

| Thành phần | Thông số |
|---|---|
| Khung hình | Dọc 9:16, 1080x1920, 30fps, quay 1 lần liền bằng camera trước, góc ngang mắt, chính diện |
| Bối cảnh | Tường sáng + cây xanh + nội thất gỗ, ánh sáng tự nhiên, không nhạc nền |
| Cắt | Jump cut bỏ hết khoảng lặng: không có đoạn im nào > 0,3s; không chuyển cảnh, không B-roll |
| Phụ đề | Hộp **vàng #FFDC00**, **bo góc** ~26px, chữ **đen** đậm, sans-serif, căn giữa |
| Vị trí phụ đề | Tâm hộp ở **~78% chiều cao** (y ≈ 1504/1920), vùng ngực người nói; rộng tối đa ~920px |
| Cỡ chữ | ~56px trên 1920px; tối đa 2 dòng; mỗi câu hiện **1,5–2 giây** (~5–8 từ) |
| Âm thanh | Chỉ giọng nói. Bản gốc −20,8 LUFS (hơi nhỏ) → skill chuẩn hoá về **−14 LUFS** |
| Bố cục nội dung | Chào + tên nhà máy → nhận xét → thông tin công ty → vị trí tuyển → lương/thưởng → diện visa & lịch phỏng vấn → yêu cầu ngành → kêu gọi inbox |

Những điểm skill **cải tiến thêm** so với bản gốc (vì đây là điểm yếu của video mẫu):
1. **Hook 3 giây đầu**: con số hấp dẫn nhất (lương, số lượng tuyển, ngày phỏng vấn) hiện chữ to phía trên, vì bản gốc tới giây 38 mới nói lương.
2. **CTA cố định 3 giây cuối** ("Inbox chị … để được hỗ trợ").
3. **Zoom xen kẽ 100% / 108%** giữa các đoạn cắt để che vết giật của jump cut.
4. **Soát lỗi phụ đề** do nhận giọng tự động (xem mục 4).
5. Âm lượng chuẩn −14 LUFS.

## 2. Cần có

- `ffmpeg` + `ffprobe` (macOS: `brew install ffmpeg`)
- Python 3 + Pillow (`pip install pillow`)
- Phụ đề dạng SRT: xuất từ CapCut (Phụ đề tự động → Xuất SRT) **hoặc** dùng Whisper:
  `pip install openai-whisper` rồi `whisper cut.mp4 --language vi --model medium --output_format srt`
- Font có dấu tiếng Việt: script tự tìm Arial Bold (macOS/Windows) / Inter / DejaVu; có thể truyền `--font`.

## 3. Quy trình (Claude làm theo thứ tự này)

Đặt `S=<thư mục skill>/scripts/edit_video.py`.

**Bước 0 – Lấy & kiểm tra video.** Nếu video nằm trên Google Drive/máy người dùng, tải về
thư mục làm việc. Kiểm tra: `ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate in.mp4`.
Video ngang → hỏi người dùng có muốn crop dọc không trước khi làm.

**Bước 1 – Cắt khoảng lặng:**
```
python3 $S cut in.mp4 cut.mp4 --zoom
```
- `--noise -35` (dB) và `--min-silence 0.35` (giây) là mặc định giống nhịp video mẫu.
  Phòng ồn → `--noise -30`; người nói chậm, bị cắt mất chữ → tăng `--pad 0.12`.
- Bỏ `--zoom` nếu người dùng muốn giữ khung hình đứng yên như bản gốc.
- Ngoài khoảng lặng, **cắt tay các câu nói lặp/nói vấp** nếu người dùng chỉ ra (vd. bản gốc nói
  "hôm nay review một nhà máy" ở giây 0 rồi lặp "hôm nay giới thiệu một nhà máy" ở giây 16):
  `ffmpeg -i cut.mp4 -vf "select='not(between(t,16,18))',setpts=N/FRAME_RATE/TB" -af "aselect='not(between(t,16,18))',asetpts=N/SR/TB" cut_b.mp4`

**Bước 2 – Phụ đề SRT cho `cut.mp4`** (phải tạo từ video ĐÃ cắt để khớp thời gian).
Sau đó chia câu dài thành cụm ngắn đúng nhịp mẫu (≤ 8 từ):
```
python3 $S split-srt cut.srt cut_short.srt --max-words 8
```

**Bước 3 – Soát lỗi phụ đề** (bắt buộc – xem mục 4). Sửa trực tiếp trong file SRT,
đưa danh sách chỗ sửa cho người dùng duyệt nếu không chắc.

**Bước 4 – Dựng bản cuối:**
```
python3 $S render cut.mp4 final.mp4 --srt cut_short.srt \
  --hook "LƯƠNG 21 TRIỆU|Tuyển 2 kỹ sư đi Nhật – PV 20/10" \
  --cta "Inbox chị Hằng để được hỗ trợ"
```
- `--hook "DÒNG TO|dòng phụ"`: dòng to hộp vàng + dòng phụ hộp trắng, ở 1/5 trên màn hình, 3 giây.
  Hook lấy từ **con số hấp dẫn nhất** trong lời nói (lương, số lượng, ngày phỏng vấn, tên tỉnh). Hỏi người dùng nếu không chắc.
- `--cta`: hiện 3 giây cuối. Emoji sẽ bị bỏ (font không hỗ trợ).
- Xem thử kiểu chữ không cần video: `python3 $S preview "câu thử" preview.png`

**Bước 5 – Kiểm tra chất lượng trước khi giao:**
- Trích ảnh để tự xem: `ffmpeg -i final.mp4 -vf "fps=1,scale=216:-1,tile=6x2" sheet_%02d.jpg`
  → kiểm tra phụ đề không che mặt, không tràn hộp, hook/CTA đúng chữ.
- Kiểm tra âm lượng: `ffmpeg -i final.mp4 -af ebur128 -f null - 2>&1 | grep -A3 Summary` → I ≈ −14 LUFS.
- Báo lại cho người dùng: độ dài trước/sau, số đoạn đã cắt, danh sách lỗi phụ đề đã sửa.

## 4. Checklist soát phụ đề (lỗi thật gặp trong video mẫu)

Nhận giọng tự động hay sai ở các chỗ sau – luôn kiểm tra:
- **Tên riêng / địa danh Nhật**: "Ymanashi" → "Yamanashi"; tên thành phố, tên công ty phải đúng chính tả.
- **Con số & đơn vị**: "21 M" → "21 triệu"; "hai mươi 20/10" → "20/10"; "mười năm triệu" → kiểm tra lại số (15 triệu yên?).
- **Từ bị tách/dính**: "t ầm" → "tầm"; "xây dựng it" → "xây dựng, IT".
- **Từ đầu câu bị mất/sai**: "sư sang làm" → "kỹ sư sang làm"; "man chưa bao gồm" → "lương chưa bao gồm"; "yên lĩnh vực" → "còn lĩnh vực".
- **Từ đệm thừa**: "à", "thì", "là" lặp liên tục – có thể bỏ khỏi phụ đề cho gọn (không cần cắt tiếng).
- **Câu mất phụ đề**: mọi đoạn có tiếng nói đều phải có phụ đề (bản gốc bị trống ở ~giây 48 và 54–56).

## 5. Làm tay trong CapCut (cho người không dùng dòng lệnh)

1. Tạo dự án mới 9:16, nhập video.
2. Chọn clip → **Xóa khoảng lặng / Remove silences** (hoặc tự cắt bằng phím tách `Ctrl/⌘+B` tại chỗ ngắt hơi).
3. Mỗi đoạn lẻ (đoạn 2, 4, 6…): **Phóng to 108%** để che vết giật.
4. **Văn bản → Phụ đề tự động** (Tiếng Việt). Soát lỗi theo mục 4.
5. Kiểu phụ đề: font sans đậm (vd. *Montserrat SemiBold* / *Be Vietnam Pro*), cỡ ~ 8–9,
   chữ **đen #000000**, **Nền bật**, màu nền **#FFDC00**, độ mờ 100%, **bo góc** cao;
   kéo phụ đề xuống ~**3/4 màn hình** (ngang ngực người nói); tối đa 2 dòng; áp dụng cho tất cả.
6. Thêm **Văn bản** hook ở 3 giây đầu (chữ to, cùng kiểu hộp vàng, đặt phía trên đầu người nói).
7. Thêm **Văn bản** CTA ở 3 giây cuối: "Inbox chị … để được hỗ trợ".
8. Âm thanh → **Chuẩn hóa độ lớn** (Normalize loudness).
9. Xuất 1080p, 30fps.

## 6. Gợi ý nâng cấp (đề xuất cho người dùng, không tự làm nếu không được yêu cầu)

- Chèn 3–5 ảnh/clip thực tế nhà máy (1–2s mỗi cảnh) khi người nói nhắc tới "hình ảnh nhà máy", "môi trường làm việc".
- Làm nổi các con số (lương, ngày phỏng vấn) bằng chữ to/màu khác hiệu ứng nảy.
- Nhạc nền nhẹ ở mức −25 đến −30 dB so với giọng.
- Tăng nhẹ tương phản + độ ấm nếu da bị xám.
