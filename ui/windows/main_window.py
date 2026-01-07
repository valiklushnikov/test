import tkinter as tk
from tkinter import ttk
from ui.frames.status_frame import StatusFrame
from ui.frames.prices_frame import PricesFrame
from ui.frames.positions_frame import PositionsFrame
from ui.frames.orders_frame import OrdersFrame
from ui.frames.log_frame import LogFrame
import threading


class MainWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self._set_geometry(1000, 600)
        root.minsize(1000, 600)

        self._setup_style()

        # === Верхняя строка статуса ===
        top = ttk.Frame(root)
        top.grid(row=0, column=0, sticky="ew", padx=4, pady=2)
        top.columnconfigure(0, weight=1)

        self.status = StatusFrame(top, app)
        self.status.grid(row=0, column=0, sticky="w")

        btn = ttk.Button(top, text="Настройки", command=self.open_settings)
        btn.grid(row=0, column=1, sticky="e", padx=4)

        # === Основная панель (трехколоночная) ===
        paned = ttk.Panedwindow(root, orient="horizontal")
        paned.grid(row=1, column=0, sticky="nsew", padx=4, pady=2)
        root.rowconfigure(1, weight=1)
        root.columnconfigure(0, weight=1)

        # ===== Левая колонка: Цены =====
        left = ttk.Frame(paned)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        self.prices = PricesFrame(left, app)
        self.prices.grid(row=0, column=0, sticky="nsew")

        paned.add(left, weight=1)

        # ===== Центральная колонка: Notebook =====
        center = ttk.Frame(paned)
        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(center)
        notebook.grid(row=0, column=0, sticky="nsew")

        # --- Вкладка 1: Позиции ---
        positions_tab = ttk.Frame(notebook)
        positions_tab.rowconfigure(0, weight=1)
        positions_tab.columnconfigure(0, weight=1)

        self.positions = PositionsFrame(positions_tab, app)
        self.positions.grid(row=0, column=0, sticky="nsew")

        notebook.add(positions_tab, text="Позиции")

        # --- Вкладка 2: Ордера ---
        orders_tab = ttk.Frame(notebook)
        orders_tab.rowconfigure(0, weight=1)
        orders_tab.columnconfigure(0, weight=1)

        self.orders = OrdersFrame(orders_tab, app)
        self.orders.grid(row=0, column=0, sticky="nsew")

        notebook.add(orders_tab, text="Ордера")

        paned.add(center, weight=3)

        # === Лог внизу ===
        self.log = LogFrame(root, app)
        self.log.grid(row=2, column=0, sticky="ew", padx=4, pady=2)
        root.rowconfigure(2, weight=0)

        # === Подписываемся на события ===
        self.app.events.subscribe("on_price_updated", self._on_price_updated)
        self.app.events.subscribe("on_balance_updated", self._on_balance_updated)
        self.app.events.subscribe("on_positions_updated", self._on_positions_updated)
        self.app.events.subscribe("on_orders_updated", self._on_orders_updated)
        self.app.events.subscribe("on_api_status", self._on_api_status)
        self.app.events.subscribe("on_bybit_status", self._on_bybit_status)

        # Запускаем инициализацию в фоновом потоке
        threading.Thread(target=self._initialize_async, daemon=True).start()

    def _initialize_async(self):
        """Асинхронная инициализация приложения"""
        try:
            # 1. Настройка Bybit (это может занять время)
            self.app.configure_bybit()

            # 2. Старт приложения (запуск scheduler и задач)
            self.app.start()

            self.app.logger.info("MainWindow инициализирован")
        except Exception as e:
            self.app.logger.error("Ошибка инициализации MainWindow", {"error": str(e)})

    def _on_bybit_status(self, data):
        status = data.get("status", False)
        self.root.after(0, lambda s=status: self.status.set_bybit_status(s))

    def _on_api_status(self, data):
        status = data.get("status", False)
        self.root.after(0, lambda s=status: self.status.set_api_status(s))

    def _on_price_updated(self, data):
        self.root.after(0, lambda d=dict(data): self.prices.update_prices(d))

    def _on_balance_updated(self, data):
        wallet = data.get("wallet", 0.0)
        trading = self.app.balance_service.trading_balance
        self.root.after(0, lambda w=wallet, t=trading: self.status.update_balance(w, t))

    def _on_positions_updated(self, data):
        positions = list(data)
        self.root.after(0, lambda p=positions: self.positions.update(p))

    def _on_orders_updated(self, data):
        """Обработчик обновления ордеров"""
        orders = list(data)
        self.root.after(0, lambda o=orders: self.orders.update(o))

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