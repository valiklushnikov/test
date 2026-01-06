import tkinter as tk
from tkinter import ttk


class LogFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        # Только вертикальный скролл, высота 4 строки
        self.text = tk.Text(self, height=4, state="disabled")
        vs = ttk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=vs.set)
        self.text.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.buffer = []
        self.app.events.subscribe("on_ui_log", self._on_log)

    def _on_log(self, data):
        level = data.get("level", "INFO")
        msg = data.get("message", "")
        extra = data.get("data", {})
        ts = data.get("ts")
        tstr = ""
        if isinstance(ts, int):
            hh = (ts // 1000) % 86400 // 3600
            mm = (ts // 1000) % 3600 // 60
            ss = (ts // 1000) % 60
            tstr = f"[{hh:02d}:{mm:02d}:{ss:02d}] "
        self._append(level, tstr + msg, extra)

    def _append(self, level, message, data):
        try:
            line = f"[{level}] {message}"
            if data:
                line += f" {data}"
            self.buffer.append(line)
            if len(self.buffer) > 100:
                self.buffer = self.buffer[-100:]
            self.text.configure(state="normal")
            self.text.delete("1.0", "end")
            self.text.insert("end", "\n".join(self.buffer) + "\n")
            self.text.configure(state="disabled")
            self.text.see("end")
        except Exception:
            pass