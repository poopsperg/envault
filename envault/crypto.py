"""Encryption and decryption utilities for envault using AES-GCM."""

import os
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 390000
MIN_PAYLOAD_SIZE = SALT_SIZE + NONCE_SIZE + 16  # 16 bytes = AES-GCM auth tag


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a passphrase and salt using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def encrypt(plaintext: str, passphrase: str) -> str:
    """Encrypt plaintext string and return a base64-encoded payload.

    Format: base64(salt || nonce || ciphertext_with_tag)
    """
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(passphrase, salt)

    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    payload = salt + nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt(encoded_payload: str, passphrase: str) -> str:
    """Decrypt a base64-encoded payload and return the plaintext string."""
    try:
        payload = base64.b64decode(encoded_payload.encode("utf-8"))
    except Exception as exc:
        raise ValueError("Invalid encrypted payload: bad base64 encoding.") from exc

    if len(payload) < MIN_PAYLOAD_SIZE:
        raise ValueError(
            f"Invalid encrypted payload: too short "
            f"(got {len(payload)} bytes, need at least {MIN_PAYLOAD_SIZE})."
        )

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = payload[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(passphrase, salt)
    aesgcm = AESGCM(key)

    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed: wrong passphrase or corrupted data.") from exc

    return plaintext.decode("utf-8")
