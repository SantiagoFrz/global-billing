from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet
from django.conf import settings


def _fernet() -> Fernet:
    if settings.FIELD_ENCRYPTION_KEY:
        key = settings.FIELD_ENCRYPTION_KEY.encode()
    else:
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(secret: str) -> bytes:
    return _fernet().encrypt(secret.encode())


def decrypt_secret(encrypted: bytes) -> str:
    return _fernet().decrypt(bytes(encrypted)).decode()
