#!/bin/bash
set -e

CLIENT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"
USER_ID="$(id -u)"

echo "Setting up PiScreen client service..."
echo "  Client directory : $CLIENT_DIR"
echo "  User             : $USER_NAME (uid=$USER_ID)"
echo ""

sudo usermod -aG video,render "$USER_NAME"

sudo tee /etc/systemd/system/piscreen.service > /dev/null << EOF
[Unit]
Description=PiScreen Media Display
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 -u $CLIENT_DIR/Client.py
WorkingDirectory=$CLIENT_DIR
Restart=always
RestartSec=5
User=$USER_NAME
Environment=SDL_VIDEODRIVER=kmsdrm

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piscreen
sudo systemctl restart piscreen

echo ""
echo "Done. Service status:"
sudo systemctl status piscreen --no-pager
