#!/bin/bash
# Server setup script for Thai2Chinese webhook deployment

set -e

echo "=== Thai2Chinese Webhook Setup ==="

# 1. Update system
echo "[1/7] Updating system..."
apt update && apt upgrade -y

# 2. Install Python and dependencies
echo "[2/7] Installing Python..."
apt install -y python3 python3-pip python3-venv git

# 3. Create non-root service user
echo "[3/7] Creating service user..."
if ! id -u thaiword >/dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin -d /opt/thaiword -m thaiword
fi

# 4. Clone repository
echo "[4/7] Cloning repository..."
if [ ! -d /opt/thaiword/app ]; then
    git clone https://github.com/Ifycyu/Thai2Chinese.git /opt/thaiword/app
fi
cd /opt/thaiword/app

# 5. Setup Python environment
echo "[5/7] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set ownership
chown -R thaiword:thaiword /opt/thaiword

# 6. Create systemd service for the app
echo "[6/7] Creating systemd service..."
cat > /etc/systemd/system/thai2chinese.service << EOF
[Unit]
Description=Thai2Chinese Application
After=network.target

[Service]
Type=simple
User=thaiword
WorkingDirectory=/opt/thaiword/app
Environment="PATH=/opt/thaiword/app/venv/bin"
ExecStart=/opt/thaiword/app/venv/bin/python run.py
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# 7. Create systemd service for webhook
echo "[7/7] Creating webhook service..."
cat > /etc/systemd/system/thai2chinese-webhook.service << EOF
[Unit]
Description=Thai2Chinese Webhook Receiver
After=network.target

[Service]
Type=simple
User=thaiword
WorkingDirectory=/opt/thaiword/app
Environment="PATH=/opt/thaiword/app/venv/bin"
Environment="WEBHOOK_SECRET=CHANGE_ME_TO_A_REAL_SECRET"
Environment="PROJECT_DIR=/opt/thaiword/app"
Environment="RESTART_COMMAND=systemctl restart thai2chinese"
ExecStart=/opt/thaiword/app/venv/bin/python scripts/webhook.py
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable thai2chinese
systemctl enable thai2chinese-webhook
systemctl start thai2chinese
systemctl start thai2chinese-webhook

echo ""
echo "=== Setup Complete ==="
echo "Thai2Chinese app: http://YOUR_SERVER_IP:8082"
echo "Webhook URL: http://YOUR_SERVER_IP:9000/webhook"
echo ""
echo "IMPORTANT: Edit /etc/systemd/system/thai2chinese-webhook.service"
echo "and set a real WEBHOOK_SECRET before using the webhook."
echo ""
echo "Next steps:"
echo "1. Set a real WEBHOOK_SECRET in the webhook service file"
echo "2. Add webhook in GitHub Settings:"
echo "   URL: http://YOUR_SERVER_IP:9000/webhook"
echo "   Secret: (the secret you set as WEBHOOK_SECRET)"
echo "   Content type: application/json"
echo "   Events: Just the push event"
echo "3. Test by pushing code to GitHub"
