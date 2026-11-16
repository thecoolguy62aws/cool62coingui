#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2026 thecoolguy62aws
# SPDX-License-Identifier: AGPL-3.0-or-later

_cool62coin_uninstall() {
    local SCRIPT_PATH="${BASH_SOURCE[0]}"
    local APP_DIR
    APP_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

    if [ "$EUID" -ne 0 ]; then
        echo "Requesting administrative privileges..."
        if sudo -v; then
            sudo bash "$SCRIPT_PATH" "$@"
            return $?
        else
            echo "Root privileges are required to uninstall cool62coin Wallet."
            return 1
        fi
    fi

    cd "$APP_DIR" || return 1

    echo "  Uninstalling cool62coin Wallet"
    echo ""
    echo "Current Directory: $(pwd)"
    echo ""

    echo "[1/2] Removing virtual environment..."
    rm -rf "$APP_DIR/venv" || return 1
    echo ""

    echo "[2/2] Removing Application Menu Shortcut..."
    local DESKTOP_FILE="/usr/share/applications/cool62coin-wallet.desktop"
    rm -f "$DESKTOP_FILE" || return 1
    echo ""

    echo "  Uninstalled. Your wallet files haven't been deleted, so if you choose to reinstall, your accounts will still be there."
    echo ""
    read -n 1 -s -r -p "Press any key to exit..."
    echo ""
}

_cool62coin_uninstall "$@"
unset -f _cool62coin_uninstall
