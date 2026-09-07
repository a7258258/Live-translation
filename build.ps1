$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -U pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
& .\.venv\Scripts\pyinstaller.exe --noconfirm Live-translation.spec

Write-Host "完成：dist\Live-translation\Live-translation.exe"
