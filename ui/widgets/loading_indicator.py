from tkinter import ttk


class LoadingIndicator:
    """Индикатор загрузки"""

    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.label = ttk.Label(self.frame, text="Загрузка...")
        self.label.pack()

        self.progress = ttk.Progressbar(
            self.frame,
            mode='indeterminate',
            length=200
        )
        self.progress.pack(pady=5)

    def show(self, message: str = "Загрузка..."):
        """Показать индикатор"""
        self.label.config(text=message)
        self.frame.pack(expand=True)
        self.progress.start(10)

    def hide(self):
        """Скрыть индикатор"""
        self.progress.stop()
        self.frame.pack_forget()