"""
External API encryption helper
Use this to encrypt headers when calling ThaiWord API from outside the web app
"""
import base64
import os
import json
import urllib.request
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(secret: str) -> bytes:
    """Derive AES key from secret string."""
    salt = b"ThaiWordSalt"
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(secret.encode())


def encrypt_text(text: str, secret: str) -> str:
    """Encrypt text using AES-GCM."""
    if not secret or not text:
        return text

    key = derive_key(secret)
    iv = os.urandom(12)
    aesgcm = AESGCM(key)
    encrypted = aesgcm.encrypt(iv, text.encode(), None)

    # Combine IV + encrypted data and base64 encode
    combined = iv + encrypted
    return base64.b64encode(combined).decode()


def make_request(url: str, secret: str, dict_api: str = "",
                 translate_endpoint: str = "", translate_token: str = "",
                 translate_model: str = "") -> dict:
    """Make encrypted API request."""
    headers = {
        "Content-Type": "application/json",
        "X-Encrypted": "true" if secret else "false",
    }

    if secret:
        if dict_api:
            headers["X-Dict-API"] = encrypt_text(dict_api, secret)
        if translate_endpoint:
            headers["X-Translate-Endpoint"] = encrypt_text(translate_endpoint, secret)
        if translate_token:
            headers["X-Translate-Token"] = encrypt_text(translate_token, secret)
    else:
        if dict_api:
            headers["X-Dict-API"] = dict_api
        if translate_endpoint:
            headers["X-Translate-Endpoint"] = translate_endpoint
        if translate_token:
            headers["X-Translate-Token"] = translate_token

    if translate_model:
        headers["X-Translate-Model"] = translate_model

    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode("utf-8"))


# ========== Usage Examples ==========

if __name__ == "__main__":
    BASE_URL = "http://localhost:8082/api/v1"
    SECRET = "your-secret-key"

    # Example 1: Dictionary lookup (encrypted)
    print("=== Dictionary Lookup ===")
    result = make_request(
        url=f"{BASE_URL}/dict/สวัสดี",
        secret=SECRET,
        dict_api="https://xcxapi.seak.online/wxapi//t1/t2cv2?tp=1&userid=xxx&useridkey=xxx"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Example 2: Translate (encrypted)
    print("\n=== Translate ===")
    result = make_request(
        url=f"{BASE_URL}/translate?sentence=ไปเที่ยวตลาด",
        secret=SECRET,
        translate_endpoint="https://token-plan-sgp.xiaomimimo.com/anthropic/v1/messages",
        translate_token="tp-so9m2glxxxxxx",
        translate_model="mimo-v2.5-pro"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Example 3: Split (no encryption needed)
    print("\n=== Split ===")
    result = make_request(
        url=f"{BASE_URL}/split?sentence=ไปเที่ยวตลาด",
        secret=""
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
