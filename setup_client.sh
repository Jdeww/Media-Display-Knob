#!/bin/bash
set -e

CLIENT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"
USER_ID="$(id -u)"

echo "Setting up PiScreen client service..."
echo "  Client directory : $CLIENT_DIR"
echo "  User             : $USER_NAME (uid=$USER_ID)"
echo ""

sudo tee /etc/systemd/system/piscreen.service > /dev/null << EOF
[Unit]
Description=PiScreen Media Display
After=graphical.target network-online.target
Wants=network-online.target

[Service]
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/python3 -u $CLIENT_DIR/Client.py
WorkingDirectory=$CLIENT_DIR
Restart=always
RestartSec=5
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority
Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID

[Install]
WantedBy=graphical.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable piscreen
sudo systemctl restart piscreen

echo ""
echo "Done. Service status:"
sudo systemctl status piscreen --no-pager
