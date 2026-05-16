"""
GitHub Webhook receiver
When GitHub sends a push event, this script pulls the latest code and restarts the service.

Usage:
1. Run this script on your server: python scripts/webhook.py
2. In GitHub repo settings, add webhook: http://your-server:9000/webhook
"""
import os
import subprocess
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Configuration - 从环境变量读取，不写在代码里
import os

WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", 9000))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")  # 从环境变量读取
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/root/python/Thai2Chinese")
RESTART_COMMAND = os.environ.get("RESTART_COMMAND", "systemctl restart thai2chinese")

# 如果不用 systemd，用这个命令代替：
# RESTART_COMMAND = "pkill -f 'python run.py' && cd /root/Thai2Chinese && nohup venv/bin/python run.py > app.log 2>&1 &"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Verify signature (optional but recommended)
        signature = self.headers.get("X-Hub-Signature-256", "")
        if WEBHOOK_SECRET and signature:
            expected = "sha256=" + hmac.new(
                WEBHOOK_SECRET.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected):
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Invalid signature")
                return

        # Parse event
        event = self.headers.get("X-GitHub-Event", "")
        if event == "push":
            try:
                # Pull latest code
                subprocess.run(
                    ["git", "pull", "origin", "main"],
                    cwd=PROJECT_DIR,
                    check=True,
                    capture_output=True
                )

                # Install dependencies if requirements.txt changed
                subprocess.run(
                    ["pip", "install", "-r", "requirements.txt"],
                    cwd=PROJECT_DIR,
                    check=True,
                    capture_output=True
                )

                # Restart service
                subprocess.run(
                    RESTART_COMMAND.split(),
                    check=True,
                    capture_output=True
                )

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK - Deployed successfully")
                print(f"Deployed successfully at {__import__('datetime').datetime.now()}")

            except subprocess.CalledProcessError as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())
                print(f"Deployment failed: {e}")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f"Ignored event: {event}".encode())

    def log_message(self, format, *args):
        print(f"[Webhook] {format % args}")


def main():
    server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    print(f"Webhook server running on port {WEBHOOK_PORT}")
    print(f"Project directory: {PROJECT_DIR}")
    print(f"Add this webhook URL in GitHub: http://your-server:{WEBHOOK_PORT}/webhook")
    server.serve_forever()


if __name__ == "__main__":
    main()
