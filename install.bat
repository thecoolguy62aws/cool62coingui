@echo off
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

echo   Installing cool62coin Wallet
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
curl -L "https://dist.torproject.org/torbrowser/15.0.26/tor-expert-bundle-windows-x86_64-15.0.26.tar.gz" --output "%TEMP%\cool62coingui-tor-expert-bundle.tar.gz"
mkdir "%TEMP%\cool62coingui-tor-expert-bundle"
tar -xzf "%TEMP%\cool62coingui-tor-expert-bundle.tar.gz" -C "%TEMP%\cool62coingui-tor-expert-bundle"
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
echo   Installation Success!
echo.
pause
