# Cai skill edit-video-bds cho Claude Code tren Windows (PowerShell).
#   - Tu goi cai da giai nen: bam dup CAI-DAT-WINDOWS.bat
#   - Hoac cai thang tu GitHub:
#     irm https://raw.githubusercontent.com/trungkienfb98/trun/claude/cool-fermat-yyoi8g/installer/install-edit-video-bds.ps1 | iex
# Bien moi truong tuy chon: EVB_REF (nhanh GitHub), EVB_SKIP_MODEL=1 (khong tai truoc model chep loi).
$ErrorActionPreference = 'Stop'
$Repo = 'trungkienfb98/trun'
$Ref = if ($env:EVB_REF) { $env:EVB_REF } else { 'claude/cool-fermat-yyoi8g' }
$Dest = Join-Path $env:USERPROFILE '.claude\skills\edit-video-bds'

function Say($m) { Write-Host "==> $m" }
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine') + ";$env:USERPROFILE\.local\bin" }

# 1. Python 3.9+ (bo qua ban gia "python" cua Microsoft Store)
$script:PyExe = $null; $script:PyArgs = @()
function Find-Python {
    foreach ($c in @('py', 'python', 'python3')) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            $extra = if ($c -eq 'py') { @('-3') } else { @() }
            try { & $c @extra -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>$null } catch { continue }
            if ($LASTEXITCODE -eq 0) { $script:PyExe = $c; $script:PyArgs = $extra; return $true }
        }
    }
    return $false
}
if (-not (Find-Python)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Say 'Dang cai Python 3.12 bang winget...'
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
        Refresh-Path
    }
    if (-not (Find-Python)) { throw 'Chua co Python 3.9+. Cai tai https://www.python.org/downloads/ (tick "Add python.exe to PATH") roi chay lai.' }
}
function Run-Py { & $script:PyExe @script:PyArgs @args }
Say "Python: $(Run-Py --version)"

# 2. Thu vien Python (ffmpeg di kem qua imageio-ffmpeg)
Say 'Dang cai thu vien: pillow numpy sherpa-onnx imageio-ffmpeg'
Run-Py -m pip install --user -q --upgrade pillow numpy sherpa-onnx imageio-ffmpeg
if ($LASTEXITCODE -ne 0) { throw 'Cai thu vien Python that bai.' }

# 3. Lay file skill: uu tien thu muc canh script, khong co thi tai tu GitHub
$Src = $null; $Tmp = $null
if ($PSScriptRoot) {
    foreach ($d in @((Join-Path $PSScriptRoot 'edit-video-bds'), (Join-Path $PSScriptRoot '..\.claude\skills\edit-video-bds'))) {
        if (Test-Path (Join-Path $d 'SKILL.md')) { $Src = (Resolve-Path $d).Path; break }
    }
}
if (-not $Src) {
    Say "Dang tai skill tu GitHub ($Ref)..."
    $Tmp = Join-Path $env:TEMP ("evb-" + [guid]::NewGuid())
    New-Item -ItemType Directory -Path $Tmp | Out-Null
    $Zip = Join-Path $Tmp 'src.zip'
    Invoke-WebRequest -UseBasicParsing "https://codeload.github.com/$Repo/zip/refs/heads/$Ref" -OutFile $Zip
    Expand-Archive $Zip -DestinationPath $Tmp
    $Skill = Get-ChildItem -Path $Tmp -Recurse -Filter SKILL.md | Where-Object { $_.Directory.Name -eq 'edit-video-bds' } | Select-Object -First 1
    if (-not $Skill) { throw 'Khong tim thay skill trong ban tai ve.' }
    $Src = $Skill.Directory.FullName
}

# 4. Chep vao %USERPROFILE%\.claude\skills (giu ban cu lam backup)
New-Item -ItemType Directory -Force -Path (Split-Path $Dest) | Out-Null
if (Test-Path $Dest) {
    $Bk = "$Dest.bak-$(Get-Date -Format yyyyMMddHHmmss)"
    Move-Item $Dest $Bk; Say "Ban cu duoc luu o $Bk"
}
Copy-Item -Recurse $Src $Dest
Get-ChildItem $Dest -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
if ($Tmp) { Remove-Item -Recurse -Force $Tmp }
Say "Da cai skill vao $Dest"

$Scripts = (Join-Path $Dest 'scripts') -replace '\\', '/'
# 5. Tai truoc model chep loi tieng Viet (~260 MB)
if ($env:EVB_SKIP_MODEL -ne '1') {
    Say 'Dang tai model chep loi tieng Viet (~260 MB, chi 1 lan)...'
    Run-Py -c "import sys; sys.path.insert(0, '$Scripts'); import transcribe; print(transcribe.ensure_model())"
    if ($LASTEXITCODE -ne 0) { Write-Host '   (Chua tai duoc model, skill se thu lai khi dung lan dau.)' }
}

# 6. Kiem tra nhanh
Run-Py -c "import sys; sys.path.insert(0, '$Scripts'); import common, PIL, numpy; print('   ffmpeg:', common.ffmpeg_exe())"

Write-Host ''
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Say 'Xong! Mo Claude Code, gui video va go: /edit-video-bds'
} else {
    Say 'Xong phan skill. May chua co Claude Code, cai bang lenh PowerShell:'
    Write-Host '    irm https://claude.ai/install.ps1 | iex'
    Write-Host "    roi chay 'claude', gui video va go: /edit-video-bds"
}
