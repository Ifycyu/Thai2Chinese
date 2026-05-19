"""
Lightweight GitHub Webhook receiver
Only uses standard library - no heavy imports
"""
import os
import subprocess
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration from environment variables
WEBHOOK_PORT = int(os.environ.get("WEBHOOK_PORT", 9000))
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/root/python/Thai2Chinese")
RESTART_COMMAND = os.environ.get("RESTART_COMMAND", "/usr/bin/systemctl restart thai2chinese")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        if not WEBHOOK_SECRET:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Webhook secret not configured")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 65536:
            self.send_response(413)
            self.end_headers()
            return

        body = self.rfile.read(content_length)

        # Verify signature (mandatory)
        signature = self.headers.get("X-Hub-Signature-256", "")
        if not signature:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Missing signature")
            return

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

        event = self.headers.get("X-GitHub-Event", "")
        if event == "push":
            try:
                subprocess.run(
                    ["/usr/bin/git", "pull", "origin", "main"],
                    cwd=PROJECT_DIR,
                    check=True,
                    capture_output=True,
                    timeout=60
                )

                subprocess.run(
                    RESTART_COMMAND.split(),
                    check=True,
                    capture_output=True,
                    timeout=30
                )

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")

            except Exception:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Internal error")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Ignored")

    def log_message(self, format, *args):
        print(f"[Webhook] {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", WEBHOOK_PORT), WebhookHandler)
    print(f"Webhook running on port {WEBHOOK_PORT}")
    server.serve_forever()
