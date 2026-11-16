#!/usr/bin/env bash
# SPDX-FileCopyrightText: © 2026 thecoolguy62aws
# SPDX-License-Identifier: AGPL-3.0-or-later

_cool62coin_install() {
    local SCRIPT_PATH="${BASH_SOURCE}"
    local APP_DIR
    APP_DIR="$(cd "$(dirname "$SCRIPT_PATH")" && pwd)"

    if [ "$EUID" -ne 0 ]; then
        echo "Requesting administrative privileges..."
        if sudo -v; then
            sudo bash "$SCRIPT_PATH" "$@"
            return $?
        else
            echo "Root privileges are required to install cool62coin Wallet."
            return 1
        fi
    fi

    cd "$APP_DIR" || return 1

    echo "Installing cool62coin Wallet"
    echo ""
    echo "Current Directory: $(pwd)"
    echo ""

    echo "[1/3] Setting up Python virtual environment..."
    python3 -m venv "$APP_DIR/venv" || return 1
    source "$APP_DIR/venv/bin/activate" || return 1
    echo ""

    echo "[2/3] Installing dependencies..."
    python -m pip install --upgrade pip || return 1
    pip install . || return 1

    local ARCH
    ARCH=$(uname -m)
    local TOR_ARCH="linux-x86_64"
    if [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
        TOR_ARCH="linux-aarch64"
    elif [ "$ARCH" != "x86_64" ]; then
        echo "Warning: Unsupported architecture ($ARCH) for Tor Expert Bundle. Defaulting to x86_64."
    fi

    echo "Fetching latest Tor Expert Bundle URL for $TOR_ARCH..."
    local TOR_URL
    TOR_URL=$(python -c "
import re, urllib.request

arch = '$TOR_ARCH'
urls_to_try = [
    'https://download.torproject.org/tor/',
    'https://www.torproject.org/download/tor/'
]

found_url = ''
for page in urls_to_try:
    try:
        req = urllib.request.Request(page, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        matches = re.findall(r'https?://[^\s\"\'>]+tor-expert-bundle-' + re.escape(arch) + r'-\d+\.\d+(?:\.\d+)?\.tar\.gz', html)
        if matches:
            found_url = matches[0]
            break
    except Exception:
        pass

if not found_url:
    try:
        req = urllib.request.Request('https://dist.torproject.org/torbrowser/', headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        versions = re.findall(r'href=\"(\d+\.\d+(?:\.\d+)?)/\"', html)
        if versions:
            latest = sorted(versions, key=lambda v: [int(x) for x in v.split('.')])[-1]
            found_url = f'https://dist.torproject.org/torbrowser/{latest}/tor-expert-bundle-{arch}-{latest}.tar.gz'
    except Exception:
        pass

print(found_url)
")

    if [ -z "$TOR_URL" ]; then
        echo "Error: Could not automatically locate the latest Tor Expert Bundle URL."
        return 1
    fi

    echo "Downloading from: $TOR_URL"

    local TEMP_DIR
    TEMP_DIR=$(mktemp -d)
    local TOR_TAR="$TEMP_DIR/cool62coingui-tor-expert-bundle.tar.gz"

    curl -fL "$TOR_URL" -o "$TOR_TAR" || {
        echo "Failed to download Tor Expert Bundle."
        rm -rf "$TEMP_DIR"
        return 1
    }
    mkdir -p "$TEMP_DIR/extracted"
    tar -xzf "$TOR_TAR" -C "$TEMP_DIR/extracted" || {
        rm -rf "$TEMP_DIR"
        return 1
    }

    mkdir -p "$APP_DIR/cool62coingui"
    cp "$TEMP_DIR/extracted/tor/tor" "$APP_DIR/cool62coingui/" || {
        rm -rf "$TEMP_DIR"
        return 1
    }
    chmod +x "$APP_DIR/cool62coingui/tor"

    rm -rf "$TEMP_DIR"

    if [ -n "$SUDO_USER" ]; then
        chown -R "$SUDO_USER:$(id -gn "$SUDO_USER")" "$APP_DIR"
    fi
    echo ""

    echo "[3/3] Creating Application Menu Shortcut..."
    local DESKTOP_FILE="/usr/share/applications/cool62coin-wallet.desktop"

    cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=cool62coin Wallet
Comment=The official desktop wallet for cool62coin.
Exec="$APP_DIR/venv/bin/python" -m cool62coingui
Path=$APP_DIR
Terminal=false
Categories=Finance;Network;
EOF

    if [ -f "$APP_DIR/icon.png" ]; then
        echo "Icon=$APP_DIR/icon.png" >> "$DESKTOP_FILE"
    elif [ -f "$APP_DIR/icon.svg" ]; then
        echo "Icon=$APP_DIR/icon.svg" >> "$DESKTOP_FILE"
    elif [ -f "$APP_DIR/icon.ico" ]; then
        echo "Icon=$APP_DIR/icon.ico" >> "$DESKTOP_FILE"
    fi

    chmod 644 "$DESKTOP_FILE"
    echo ""

    echo "Installation Success!"
    echo ""
}

_cool62coin_install "$@"
unset -f _cool62coin_install
