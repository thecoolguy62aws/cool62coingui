@echo off
REM SPDX-FileCopyrightText: © 2026 thecoolguy62aws
REM SPDX-License-Identifier: AGPL-3.0-or-later

setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "try {Start-Process '%~0' -Verb RunAs; Write-Host 'Starting installer...'} catch {Write-Host 'Administrator is required to install cool62coin Wallet.'}"
    exit /b
)

cd /d "%~dp0"
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

echo Installing cool62coin Wallet
echo.
echo Current Directory: %CD%
echo.

echo [1/3] Setting up Python virtual environment...
python -m venv "%APP_DIR%\venv"
call "%APP_DIR%\venv\Scripts\activate"
echo.

echo [2/3] Installing dependencies...
python -m pip install --upgrade pip
pip install .

echo Fetching latest Tor Expert Bundle URL for windows-x86_64...
for /f "delims=" %%i in ('python -c "import re, urllib.request; arch='windows-x86_64'; pages=['https://torproject.org', 'https://torproject.org']; found=''; [found := m[0] for p in pages if not found for m in [re.findall(r'https?://[^\s\"\'>]+tor-expert-bundle-' + arch + r'-\d+\.\d+(?:\.\d+)?\.tar\.gz', urllib.request.urlopen(urllib.request.Request(p, headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read().decode('utf-8', errors='ignore'))] if m]; print(found)" 2^>nul') do set "TOR_URL=%%i"

if not defined TOR_URL (
    for /f "delims=" %%i in ('python -c "import re, urllib.request; arch='windows-x86_64'; html=urllib.request.urlopen(urllib.request.Request('https://torproject.org', headers={'User-Agent': 'Mozilla/5.0'}), timeout=15).read().decode('utf-8', errors='ignore'); versions=re.findall(r'href=\"(\d+\.\d+(?:\.\d+)?)/\"', html); latest=sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1] if versions else ''; print(f'https://torproject.org{latest}/tor-expert-bundle-{arch}-{latest}.tar.gz' if latest else '')" 2^>nul') do set "TOR_URL=%%i"
)

if not defined TOR_URL (
    echo Error: Could not automatically locate the latest Tor Expert Bundle URL.
    pause
    exit /b 1
)

echo Downloading from: !TOR_URL!
curl -fL "!TOR_URL!" --output "%TEMP%\cool62coingui-tor-expert-bundle.tar.gz"
if %errorLevel% neq 0 (
    echo Failed to download Tor Expert Bundle.
    pause
    exit /b 1
)

if exist "%TEMP%\cool62coingui-tor-expert-bundle" rmdir /s /q "%TEMP%\cool62coingui-tor-expert-bundle"
mkdir "%TEMP%\cool62coingui-tor-expert-bundle"
tar -xzf "%TEMP%\cool62coingui-tor-expert-bundle.tar.gz" -C "%TEMP%\cool62coingui-tor-expert-bundle"

if not exist "%APP_DIR%\cool62coingui" mkdir "%APP_DIR%\cool62coingui"
copy "%TEMP%\cool62coingui-tor-expert-bundle\tor\tor.exe" "%APP_DIR%\cool62coingui\"
rmdir /s /q "%TEMP%\cool62coingui-tor-expert-bundle"
del /f /q "%TEMP%\cool62coingui-tor-expert-bundle.tar.gz"
echo.

echo [3/3] Creating Windows Start Menu Shortcut...
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT_PATH=%START_MENU%\cool62coin Wallet.lnk"

powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); " ^
    "$Shortcut.TargetPath = '%APP_DIR%\venv\Scripts\pythonw.exe'; " ^
    "$Shortcut.Arguments = '-m cool62coingui'; " ^
    "$Shortcut.WorkingDirectory = '%APP_DIR%'; " ^
    "$Shortcut.Description = 'The official desktop wallet for cool62coin.'; " ^
    "if (Test-Path '%APP_DIR%\icon.ico') { $Shortcut.IconLocation = '%APP_DIR%\icon.ico' }; " ^
    "$Shortcut.Save();"
echo.

echo Installation Success!
echo.
pause
