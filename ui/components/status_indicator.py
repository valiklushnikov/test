from tkinter import ttk


class StatusIndicator(ttk.Label):
    def set_status(self, text: str):
        self.config(text=text)
