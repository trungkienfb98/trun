#!/usr/bin/env bash
# Cài Claude Code (nếu chưa có) và bật Remote Control để điều khiển máy này từ điện thoại.
# Dùng cho macOS / Linux. Chạy trong thư mục muốn làm việc, hoặc truyền đường dẫn làm tham số:
#   bash setup-remote-control.sh ~/du-an
set -euo pipefail

WORKDIR="${1:-$PWD}"
export PATH="$HOME/.local/bin:$PATH"

if ! command -v claude >/dev/null 2>&1; then
  echo "==> Đang cài Claude Code..."
  if ! curl -fsSL https://claude.ai/install.sh | bash; then
    if command -v npm >/dev/null 2>&1; then
      echo "==> Trình cài chính thất bại, thử cài bằng npm..."
      npm install -g @anthropic-ai/claude-code
    else
      echo "Không cài được Claude Code. Hãy cài Node.js (https://nodejs.org) rồi chạy lại." >&2
      exit 1
    fi
  fi
  hash -r
fi

echo "==> Claude Code: $(claude --version)"
cd "$WORKDIR"
echo "==> Thư mục làm việc: $PWD"
echo
echo "Nếu được hỏi đăng nhập, hãy đăng nhập bằng tài khoản Claude dùng trên điện thoại."
echo "Sau đó quét mã QR / mở link hiện ra, hoặc mở app Claude > Code trên điện thoại."
echo "Giữ cửa sổ này mở và máy không ngủ trong lúc điều khiển. Nhấn Ctrl+C để dừng."
echo
exec claude remote-control
