#!/usr/bin/env bash
# Cài skill edit-video-bds cho Claude Code trên macOS / Linux.
#   - Chạy từ gói cài đã giải nén:   bash install-edit-video-bds.sh
#   - Hoặc cài thẳng từ GitHub:
#     curl -fsSL https://raw.githubusercontent.com/trungkienfb98/trun/claude/cool-fermat-yyoi8g/installer/install-edit-video-bds.sh | bash
# Biến môi trường tuỳ chọn: EVB_REF (nhánh GitHub), EVB_SKIP_MODEL=1 (không tải trước model chép lời).
set -euo pipefail

REPO="trungkienfb98/trun"
REF="${EVB_REF:-claude/cool-fermat-yyoi8g}"
DEST="$HOME/.claude/skills/edit-video-bds"
export PATH="$HOME/.local/bin:$PATH"

say() { printf '==> %s\n' "$*"; }
die() { printf 'LỖI: %s\n' "$*" >&2; exit 1; }

# 1. Python 3.9+
PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  if [ "$(uname)" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
    say "Đang cài Python bằng Homebrew..."; brew install python; PY=python3
  else
    die "Chưa có Python 3.9+. Cài tại https://www.python.org/downloads/ (Linux: sudo apt install python3 python3-pip) rồi chạy lại."
  fi
fi
say "Python: $($PY --version)"

# 2. Thư viện Python (ffmpeg đi kèm qua imageio-ffmpeg nếu máy chưa có)
PKGS="pillow numpy sherpa-onnx imageio-ffmpeg"
say "Đang cài thư viện: $PKGS"
$PY -m pip --version >/dev/null 2>&1 || $PY -m ensurepip --user >/dev/null 2>&1 || die "Không có pip. Linux: sudo apt install python3-pip"
if ! $PY -m pip install --user -q --upgrade $PKGS 2>/tmp/evb-pip.log; then
  # Debian/Ubuntu mới chặn pip ngoài venv (PEP 668)
  $PY -m pip install --user -q --upgrade --break-system-packages $PKGS || { cat /tmp/evb-pip.log >&2; die "Cài thư viện thất bại."; }
fi

# 3. Lấy file skill: ưu tiên thư mục cạnh script, không có thì tải từ GitHub
SRC=""
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || true)"
for d in "$HERE/edit-video-bds" "$HERE/../.claude/skills/edit-video-bds"; do
  [ -f "$d/SKILL.md" ] && SRC="$d" && break
done
TMP=""
if [ -z "$SRC" ]; then
  say "Đang tải skill từ GitHub ($REF)..."
  TMP="$(mktemp -d)"
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF" | tar xz -C "$TMP"
  SRC="$(find "$TMP" -path '*/.claude/skills/edit-video-bds/SKILL.md' -exec dirname {} \; | head -1)"
  [ -n "$SRC" ] || die "Không tìm thấy skill trong bản tải về."
fi

# 4. Chép vào ~/.claude/skills (giữ bản cũ làm backup)
mkdir -p "$(dirname "$DEST")"
if [ -d "$DEST" ]; then
  BK="$DEST.bak-$(date +%Y%m%d%H%M%S)"; mv "$DEST" "$BK"; say "Bản cũ được lưu ở $BK"
fi
cp -R "$SRC" "$DEST"
find "$DEST" -name __pycache__ -prune -exec rm -rf {} +
[ -n "$TMP" ] && rm -rf "$TMP"
say "Đã cài skill vào $DEST"

# 5. Tải trước model chép lời tiếng Việt (~260 MB) để lần đầu dùng không phải chờ
if [ "${EVB_SKIP_MODEL:-0}" != "1" ]; then
  say "Đang tải model chép lời tiếng Việt (~260 MB, chỉ 1 lần)..."
  $PY -c "import sys; sys.path.insert(0, '$DEST/scripts'); import transcribe; print(transcribe.ensure_model())" \
    || echo "   (Chưa tải được model, skill sẽ thử lại khi dùng lần đầu.)"
fi

# 6. Kiểm tra nhanh
$PY -c "import sys; sys.path.insert(0, '$DEST/scripts'); import common, PIL, numpy; print('   ffmpeg:', common.ffmpeg_exe())"

echo
if command -v claude >/dev/null 2>&1; then
  say "Xong! Mở Claude Code, gửi video và gõ: /edit-video-bds"
else
  say "Xong phần skill. Máy chưa có Claude Code, cài bằng lệnh:"
  echo "    curl -fsSL https://claude.ai/install.sh | bash"
  echo "    rồi chạy 'claude', gửi video và gõ: /edit-video-bds"
fi
