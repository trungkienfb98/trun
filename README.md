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
