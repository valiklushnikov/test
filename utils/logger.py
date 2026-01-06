from datetime import datetime, timedelta
from pathlib import Path
import json
import os


class Logger:
    def __init__(self, logs_dir: Path, retention_days: int = 30):
        self.logs_dir = logs_dir
        self.retention_days = retention_days
        self.sink = None
        self._rotate()

    def _file_path(self):
        name = datetime.now().strftime("%Y-%m-%d") + ".log"
        return self.logs_dir / name

    def _write(self, level: str, message: str, data: dict | None = None):
        now = datetime.now()
        ts = now.strftime("%H:%M:%S")
        line = f"[{ts}] [{level}] {message}"
        if data:
            line += " " + json.dumps(data, ensure_ascii=False)
        with open(self._file_path(), "a", encoding="utf-8") as f:
            f.write(line + "\n")
        if callable(self.sink):
            try:
                self.sink(level, message, data or {}, int(now.timestamp() * 1000))
            except Exception:
                pass

    def _rotate(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for p in self.logs_dir.glob("*.log"):
            try:
                dt = datetime.strptime(p.stem, "%Y-%m-%d")
                if dt < cutoff:
                    p.unlink(missing_ok=True)
            except Exception:
                pass

    def debug(self, message: str, data: dict | None = None):
        self._write("DEBUG", message, data)

    def info(self, message: str, data: dict | None = None):
        self._write("INFO", message, data)

    def warning(self, message: str, data: dict | None = None):
        self._write("WARNING", message, data)

    def error(self, message: str, data: dict | None = None):
        self._write("ERROR", message, data)

    def set_sink(self, callback):
        self.sink = callback
