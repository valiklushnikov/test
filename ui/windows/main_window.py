import tkinter as tk
from tkinter import ttk
from ui.frames.status_frame import StatusFrame
from ui.frames.prices_frame import PricesFrame
from ui.frames.positions_frame import PositionsFrame
from ui.frames.log_frame import LogFrame


class MainWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self._set_geometry(800, 500)
        # Минимальный размер окна
        root.minsize(800, 500)
        
        # Стиль
        self._setup_style()
        # Верхняя строка статуса
        top = ttk.Frame(root)
        top.grid(row=0, column=0, sticky="ew", padx=4, pady=2)
        top.columnconfigure(0, weight=1)
        self.status = StatusFrame(top, app)
        self.status.grid(row=0, column=0, sticky="w")
        btn = ttk.Button(top, text="Настройки", command=self.open_settings)
        btn.grid(row=0, column=1, sticky="e", padx=4)
        # Основная панель
        paned = ttk.Panedwindow(root, orient="horizontal")
        paned.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)
        left = ttk.Frame(paned)
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=3)
        # Левая колонка цен
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        self.prices = PricesFrame(left, app)
        self.prices.grid(row=0, column=0, sticky="nsew")
        # Правая колонка позиций
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        self.positions = PositionsFrame(right, app)
        self.positions.grid(row=0, column=0, sticky="nsew")
        # Лог
        self.log = LogFrame(root, app)
        self.log.grid(row=2, column=0, sticky="ew", padx=4, pady=2)
        root.rowconfigure(2, weight=0)
        # События
        self.app.events.subscribe("on_price_updated", self._on_price_updated)
        self.app.events.subscribe("on_balance_updated", self._on_balance_updated)
        self.app.events.subscribe("on_positions_updated", self._on_positions_updated)
        self.app.events.subscribe("on_api_status", self._on_api_status)
        self.app.events.subscribe("on_bybit_status", self._on_bybit_status)

        # Инициализация сервисов и старт (ПОСЛЕ создания UI и подписок)
        self.app.configure_bybit()
        self.app.start()

    def _on_bybit_status(self, data):
        self.status.set_bybit_status(data.get("status", False))

    def _on_api_status(self, data):
        self.status.set_api_status(data.get("status", False))

    def _on_price_updated(self, data):
        self.prices.update_prices(data)

    def _on_balance_updated(self, data):
        self.status.update_balance(data.get("wallet", 0.0), self.app.balance_service.trading_balance)

    def _on_positions_updated(self, data):
        self.positions.update(data)

    def open_settings(self):
        from ui.windows.settings_window import SettingsWindow
        SettingsWindow(self.root, self.app)

    def _setup_style(self):
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=20)
        style.configure("TButton", font=("Segoe UI", 9))
        style.configure("TLabel", font=("Segoe UI", 9))

    def _set_geometry(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")