@echo off
setlocal enabledelayedexpansion
title Shizuku 1-Click PC Activator (Windows)
color 0E

echo ========================================================
echo    ⚡ SHIZUKU 1-CLICK PC ACTIVATOR (WINDOWS) ⚡
echo    Curated by Krishna (@kk3163019)
echo ========================================================
echo.

:: 1. Check for ADB
where adb >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] ADB not found in your system PATH.
    echo [*] Checking common Android SDK / Platform-Tools paths...
    if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" (
        set "PATH=%PATH%;%LOCALAPPDATA%\Android\Sdk\platform-tools"
        echo [+] Found ADB in Local AppData!
    ) else if exist "platform-tools\adb.exe" (
        set "PATH=%PATH%;platform-tools"
        echo [+] Found local platform-tools folder!
    ) else (
        echo [X] Could not locate adb.exe.
        echo [*] Please install Android Platform Tools from:
        echo     https://developer.android.com/tools/releases/platform-tools
        echo.
        pause
        exit /b 1
    )
)

echo [*] Checking connected Android devices...
adb start-server >nul 2>nul
adb devices
echo.

:: 2. Check if a device is connected
for /f "skip=1 tokens=1,2" %%A in ('adb devices') do (
    if "%%B"=="device" (
        set "DEVICE_FOUND=1"
        set "SERIAL=%%A"
    ) else if "%%B"=="unauthorized" (
        echo [!] Device found (%%A), but UNAUTHORIZED!
        echo [*] Check your phone screen and tap "Always allow from this computer".
        echo.
        pause
        exit /b 1
    )
)

if not defined DEVICE_FOUND (
    echo [!] No authorized Android device detected.
    echo [*] Make sure:
    echo     1. USB Cable is connected.
    echo     2. Developer Options -> USB Debugging is ON.
    echo     3. For Xiaomi / HyperOS / MIUI: Enable "USB debugging (Security settings)".
    echo.
    pause
    exit /b 1
)

echo [+] Authorized device detected: %SERIAL%
echo [*] Starting Shizuku service via ADB...
echo.

:: 3. Execute Shizuku starter commands
adb shell sh /sdcard/Android/data/moe.shizuku.privileged.api/starter.sh
if %errorlevel% neq 0 (
    echo [*] Trying alternative starter path...
    adb shell sh /data/user_de/0/moe.shizuku.privileged.api/starter.sh
)

echo.
echo ========================================================
echo    ✅ SHIZUKU ACTIVATION COMMAND SENT SUCCESSFULLY!
echo ========================================================
echo [*] Open the Shizuku app on your phone to confirm:
echo     Status should display: "Shizuku is running (ADB)"
echo.
echo [*] Explore 540+ Shizuku Apps:
echo     https://shizuku-web.onrender.com
echo     https://github.com/krishna3163/best_shizuku_apps_for_android_no_root
echo.
pause
