import json
import platform
from pathlib import Path
from utils.crypto import encrypt, decrypt


class Settings:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.path = self.data_dir / "settings.json"
        self._data = {}
        self.load()

    def _key(self) -> str:
        return platform.node() or "terminal"

    def get(self, key: str, default=None):
        val = self._data.get(key, default)
        if key in ("bybit_api_key", "bybit_api_secret") and isinstance(val, dict) and "enc" in val:
            try:
                return decrypt(val["enc"], self._key())
            except Exception:
                return ""
        return val

    def set(self, key: str, value, secure: bool = False):
        if secure and value:
            self._data[key] = {"enc": encrypt(str(value), self._key())}
        else:
            self._data[key] = value

    def delete(self, key: str):
        if key in self._data:
            del self._data[key]

    def save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            else:
                self._data = {}
        except Exception:
            self._data = {}
