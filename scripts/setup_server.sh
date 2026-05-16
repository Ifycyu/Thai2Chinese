#!/bin/bash
# Server setup script for Thai2Chinese webhook deployment

echo "=== Thai2Chinese Webhook Setup ==="

# 1. Update system
echo "[1/6] Updating system..."
apt update && apt upgrade -y

# 2. Install Python and dependencies
echo "[2/6] Installing Python..."
apt install -y python3 python3-pip python3-venv git

# 3. Clone repository
echo "[3/6] Cloning repository..."
cd /root/python
git clone https://github.com/Ifycyu/Thai2Chinese.git Thai2Chinese
cd Thai2Chinese

# 4. Setup Python environment
echo "[4/6] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Create systemd service for the app
echo "[5/6] Creating systemd service..."
cat > /etc/systemd/system/thai2chinese.service << EOF
[Unit]
Description=Thai2Chinese Application
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/python/Thai2Chinese
Environment="PATH=/root/python/Thai2Chinese/venv/bin"
ExecStart=/root/python/Thai2Chinese/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 6. Create systemd service for webhook
echo "[6/6] Creating webhook service..."
cat > /etc/systemd/system/thai2chinese-webhook.service << EOF
[Unit]
Description=Thai2Chinese Webhook Receiver
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/python/Thai2Chinese
Environment="PATH=/root/python/Thai2Chinese/venv/bin"
Environment="WEBHOOK_SECRET=你的密钥"
Environment="PROJECT_DIR=/root/python/Thai2Chinese"
Environment="RESTART_COMMAND=systemctl restart thai2chinese"
ExecStart=/root/python/Thai2Chinese/venv/bin/python scripts/webhook.py
Restart=always
RestartSec=5

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
echo "Next steps:"
echo "1. Add webhook in GitHub Settings:"
echo "   URL: http://YOUR_SERVER_IP:9000/webhook"
echo "   Secret: (the secret you set in webhook.py)"
echo "   Content type: application/json"
echo "   Events: Just the push event"
echo ""
echo "2. Test by pushing code to GitHub"
