from tkinter import ttk


class StatusFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.api_label = ttk.Label(self, text="API: ● Отключено")
        self.bybit_label = ttk.Label(self, text="Bybit: ● Отключено")
        self.balance_label = ttk.Label(self, text="Кошелёк: $0.00")
        self.trading_label = ttk.Label(self, text="Торговый: $0.00")
        self.api_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self.bybit_label.grid(row=0, column=1, sticky="w", padx=(0, 12))
        self.balance_label.grid(row=0, column=2, sticky="w", padx=(0, 12))
        self.trading_label.grid(row=0, column=3, sticky="w")
        self.columnconfigure(4, weight=1)
        
        # Initialize status from app state
        self.set_api_status(app.connected_api)
        self.set_bybit_status(app.connected_bybit)
        self.update_balance(app.balance_service.wallet_balance, app.balance_service.trading_balance)

    def update_balance(self, wallet, trading):
        self.balance_label.config(text=f"Кошелёк: ${wallet:,.2f}")
        self.trading_label.config(text=f"Торговый: ${trading:,.2f}")

    def set_api_status(self, connected: bool):
        if connected:
            self.api_label.config(text="API: ● Подключено", foreground="green")
        else:
            self.api_label.config(text="API: ● Ошибка", foreground="red")

    def set_bybit_status(self, connected: bool):
        if connected:
            self.bybit_label.config(text="Bybit: ● Подключено", foreground="green")
        else:
            self.bybit_label.config(text="Bybit: ● Ошибка", foreground="red")