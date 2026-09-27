# Cai Claude Code (neu chua co) va bat Remote Control de dieu khien may nay tu dien thoai.
# Dung cho Windows (PowerShell). Chay trong thu muc muon lam viec:
#   cd C:\du-an
#   irm https://raw.githubusercontent.com/trungkienfb98/trun/claude/phone-to-computer-control-hp8nr2/setup-remote-control.ps1 | iex
$ErrorActionPreference = 'Stop'
$env:Path = "$env:USERPROFILE\.local\bin;$env:Path"

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
    Write-Host '==> Dang cai Claude Code...'
    try {
        Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    } catch {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            Write-Host '==> Trinh cai chinh that bai, thu cai bang npm...'
            npm install -g @anthropic-ai/claude-code
        } else {
            throw 'Khong cai duoc Claude Code. Hay cai Node.js (https://nodejs.org) roi chay lai.'
        }
    }
    $env:Path = "$env:USERPROFILE\.local\bin;" + [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + [Environment]::GetEnvironmentVariable('Path', 'Machine')
}

Write-Host "==> Claude Code: $(claude --version)"
Write-Host "==> Thu muc lam viec: $(Get-Location)"
Write-Host ''
Write-Host 'Neu duoc hoi dang nhap, hay dang nhap bang tai khoan Claude dung tren dien thoai.'
Write-Host 'Sau do quet ma QR / mo link hien ra, hoac mo app Claude > Code tren dien thoai.'
Write-Host 'Giu cua so nay mo va may khong ngu trong luc dieu khien. Nhan Ctrl+C de dung.'
Write-Host ''
claude remote-control
