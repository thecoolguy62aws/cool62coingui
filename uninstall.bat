@echo off
setlocal enabledelayedexpansion

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "try {Start-Process '%~0' -Verb RunAs; Write-Host 'Starting uninstaller...'} catch {Write-Host 'Administrator is required to uninstall cool62coin Wallet.'}"
    exit /b
)

cd /d "%~dp0"
set "APP_DIR=%~dp0"
set "APP_DIR=%APP_DIR:~0,-1%"

echo   Uninstalling cool62coin Wallet
echo.
echo Current Directory: %CD%

echo.
echo [1/2] Removing virtual environment...
rmdir /S /Q "%APP_DIR%\venv"

echo.
echo [2/2] Removing Windows Start Menu Shortcut...
set "START_MENU=%ProgramData%\Microsoft\Windows\Start Menu\Programs"
set "SHORTCUT_PATH=%START_MENU%\cool62coin Wallet.lnk"

del /f /q "%SHORTCUT_PATH%"

echo.
echo   Uninstalled. Your wallet files haven't been deleted, so if you choose to reinstall, your accounts will still be there.
echo.
pause
