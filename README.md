# Điều khiển máy tính từ điện thoại bằng Claude Code (Remote Control)

Script cài Claude Code (nếu máy chưa có) rồi chạy `claude remote-control` trong thư mục hiện tại.
Sau đó bạn điều khiển phiên đó từ app Claude trên điện thoại.

## Windows

Mở **PowerShell**, chuyển vào thư mục muốn làm việc rồi dán lệnh:

```powershell
cd C:\du-an
irm https://raw.githubusercontent.com/trungkienfb98/trun/claude/phone-to-computer-control-hp8nr2/setup-remote-control.ps1 | iex
```

## macOS / Linux

Mở **Terminal** rồi chạy:

```bash
cd ~/du-an
curl -fsSL https://raw.githubusercontent.com/trungkienfb98/trun/claude/phone-to-computer-control-hp8nr2/setup-remote-control.sh | bash
```

## Sau khi chạy

1. Nếu được hỏi, đăng nhập bằng **cùng tài khoản Claude** đang dùng trên điện thoại.
2. Quét mã QR hoặc mở link hiện ra trên màn hình. Cách khác: mở app Claude, vào mục **Code** và chọn phiên đó.
3. Ra lệnh từ điện thoại. Claude sẽ làm việc trực tiếp trên máy tính.

**Lưu ý:** giữ cửa sổ terminal mở, cho máy luôn có mạng và tắt chế độ ngủ trong lúc điều khiển. Nhấn `Ctrl+C` để dừng.

# Skill edit video bất động sản (`edit-video-bds`)

Skill giúp Claude dựng video talking-head BĐS kiểu TikTok: tiêu đề hook, số đếm, thẻ dự án, ảnh sản phẩm, phụ đề tiếng Việt theo từng từ, pop/whoosh, chuẩn âm lượng. Mã nguồn nằm ở `.claude/skills/edit-video-bds/`.

## Cài cho máy khác

Windows (PowerShell):

```powershell
irm https://raw.githubusercontent.com/trungkienfb98/trun/claude/cool-fermat-yyoi8g/installer/install-edit-video-bds.ps1 | iex
```

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/trungkienfb98/trun/claude/cool-fermat-yyoi8g/installer/install-edit-video-bds.sh | bash
```

Muốn gửi gói cài offline thì chạy `bash installer/build-package.sh`. Lệnh tạo `dist/edit-video-bds-installer.zip`; người nhận giải nén rồi bấm đúp `CAI-DAT-WINDOWS.bat` hoặc chạy `install-edit-video-bds.sh`. Lệnh cũng tạo `dist/edit-video-bds.zip` để tải lên claude.ai (Cài đặt → Capabilities → Skills). Chi tiết xem `installer/HUONG-DAN.txt`.
