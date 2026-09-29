#!/usr/bin/env bash
# ========================================================
#   ⚡ SHIZUKU 1-CLICK ACTIVATOR FOR LINUX / MACOS ⚡
#   Curated by Krishna (@kk3163019)
# ========================================================

set -euo pipefail

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

echo -e "${BOLD}${YELLOW}========================================================${RESET}"
echo -e "${BOLD}${YELLOW}   ⚡ SHIZUKU 1-CLICK ACTIVATOR (LINUX / MACOS) ⚡     ${RESET}"
echo -e "${BOLD}${YELLOW}   Curated by Krishna (@kk3163019)                     ${RESET}"
echo -e "${BOLD}${YELLOW}========================================================${RESET}"
echo ""

# 1. Check for ADB
if ! command -v adb &> /dev/null; then
    echo -e "${RED}[!] ADB is not installed or not in PATH.${RESET}"
    echo -e "${YELLOW}[*] Install ADB using your package manager:${RESET}"
    echo -e "    Debian/Ubuntu: sudo apt install adb"
    echo -e "    Fedora:        sudo dnf install android-tools"
    echo -e "    Arch Linux:    sudo pacman -S android-tools"
    echo -e "    macOS:         brew install android-platform-tools"
    exit 1
fi

echo -e "${BOLD}[*] Starting ADB server & scanning connected devices...${RESET}"
adb start-server > /dev/null 2>&1 || true

DEVICES=$(adb devices | awk 'NR>1 {print $1, $2}' | grep -v '^$')

if [ -z "$DEVICES" ]; then
    echo -e "${RED}[!] No Android device detected.${RESET}"
    echo -e "${YELLOW}[*] Troubleshooting Checklist:${RESET}"
    echo -e "    1. Plug in USB cable or connect via wireless ADB."
    echo -e "    2. Developer Options -> USB Debugging is turned ON."
    echo -e "    3. Xiaomi / HyperOS / MIUI users: Enable 'USB debugging (Security settings)'."
    exit 1
fi

if echo "$DEVICES" | grep -q "unauthorized"; then
    echo -e "${RED}[!] Device detected but UNAUTHORIZED!${RESET}"
    echo -e "${YELLOW}[*] Unlock your phone and tap 'Always allow from this computer'.${RESET}"
    exit 1
fi

echo -e "${GREEN}[+] Device found & authorized!${RESET}"
echo "$DEVICES"
echo ""

# 2. Run Shizuku Starter script
echo -e "${BOLD}[*] Executing Shizuku starter process...${RESET}"

if adb shell "sh /sdcard/Android/data/moe.shizuku.privileged.api/starter.sh" 2>/dev/null; then
    echo -e "${GREEN}[+] Primary starter path succeeded!${RESET}"
else
    echo -e "${YELLOW}[*] Trying fallback user_de path...${RESET}"
    adb shell "sh /data/user_de/0/moe.shizuku.privileged.api/starter.sh"
fi

echo ""
echo -e "${BOLD}${GREEN}========================================================${RESET}"
echo -e "${BOLD}${GREEN}   ✅ SHIZUKU ACTIVATION COMMAND SENT SUCCESSFULLY!     ${RESET}"
echo -e "${BOLD}${GREEN}========================================================${RESET}"
echo -e "${BOLD}[*] Open the Shizuku app on your phone:${RESET}"
echo -e "    It should show: ${GREEN}Shizuku is running (ADB)${RESET}"
echo ""
echo -e "${BOLD}[*] Discover 540+ Shizuku Apps:${RESET}"
echo -e "    Web Portal: https://shizuku-web.onrender.com"
echo -e "    GitHub:     https://github.com/krishna3163/best_shizuku_apps_for_android_no_root"
echo ""
