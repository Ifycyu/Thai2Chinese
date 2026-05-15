"""Encryption/decryption utility for API headers."""
import os
import base64
import hashlib
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


def decrypt_text(encrypted_text: str, secret: str) -> str:
    """Decrypt base64-encoded AES-GCM encrypted text."""
    if not secret or not encrypted_text:
        return encrypted_text

    try:
        key = derive_key(secret)
        combined = base64.b64decode(encrypted_text)
        iv = combined[:12]
        data = combined[12:]
        aesgcm = AESGCM(key)
        decrypted = aesgcm.decrypt(iv, data, None)
        return decrypted.decode()
    except Exception as e:
        # If decryption fails, return as-is (might be plain text)
        return encrypted_text


def decrypt_header_value(value: str, secret: str, is_encrypted: bool) -> str:
    """Decrypt a header value if encryption is enabled."""
    if not is_encrypted or not secret:
        return value
    return decrypt_text(value, secret)
