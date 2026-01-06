import base64
import hashlib
from cryptography.fernet import Fernet


def _derive_key(key: str) -> bytes:
    h = hashlib.sha256(key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(h)


def encrypt(text: str, key: str) -> str:
    f = Fernet(_derive_key(key))
    return f.encrypt(text.encode("utf-8")).decode("utf-8")


def decrypt(encrypted: str, key: str) -> str:
    f = Fernet(_derive_key(key))
    return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")
