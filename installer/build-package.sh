#!/usr/bin/env bash
# Đóng gói bộ cài để gửi cho máy khác:
#   bash installer/build-package.sh [thư-mục-xuất]
# Tạo edit-video-bds-installer.zip (bộ cài máy tính) và edit-video-bds.zip (tải lên claude.ai).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$(mkdir -p "${1:-$ROOT/dist}" && cd "${1:-$ROOT/dist}" && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

PKG="$STAGE/edit-video-bds-installer"
mkdir -p "$PKG"
cp -R "$ROOT/.claude/skills/edit-video-bds" "$PKG/"
find "$PKG" -name __pycache__ -prune -exec rm -rf {} +
cp "$ROOT/installer/install-edit-video-bds.sh" "$ROOT/installer/install-edit-video-bds.ps1" \
   "$ROOT/installer/CAI-DAT-WINDOWS.bat" "$ROOT/installer/HUONG-DAN.txt" "$PKG/"
chmod +x "$PKG/install-edit-video-bds.sh"

(cd "$PKG" && python3 -c "
import os, zipfile
with zipfile.ZipFile('edit-video-bds.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for r, _, fs in os.walk('edit-video-bds'):
        for f in fs: z.write(os.path.join(r, f))
")
cp "$PKG/edit-video-bds.zip" "$OUT/"

(cd "$STAGE" && python3 -c "
import os, zipfile
with zipfile.ZipFile('$OUT/edit-video-bds-installer.zip', 'w', zipfile.ZIP_DEFLATED) as z:
    for r, _, fs in os.walk('edit-video-bds-installer'):
        for f in fs:
            p = os.path.join(r, f); zi = zipfile.ZipInfo.from_file(p)
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(p, 'rb') as fh: z.writestr(zi, fh.read())
")
echo "$OUT/edit-video-bds-installer.zip"
echo "$OUT/edit-video-bds.zip"
