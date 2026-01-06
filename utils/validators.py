import re
import uuid


def is_valid_uuid(uid: str) -> bool:
    try:
        uuid.UUID(uid.strip())
        return True
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s]+", url))


def is_valid_api_key(key: str) -> bool:
    return bool(key) and len(key) >= 16


def validate_trading_balance(amount: float, max_amount: float) -> bool:
    try:
        return float(amount) <= float(max_amount)
    except Exception:
        return False
