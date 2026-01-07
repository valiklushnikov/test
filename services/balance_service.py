class BalanceService:
    def __init__(self, logger):
        self.logger = logger
        self.wallet_balance = 0.0
        self.trading_balance = 0.0
        self.master_balance = 0.0
        self.bybit = None

    def set_bybit(self, bybit):
        self.bybit = bybit

    def fetch_wallet_balance(self):
        if not self.bybit:
            self.logger.warning("Bybit API не инициализирован при запросе баланса")
            return

        try:
            balance = float(self.bybit.get_balance())
            self.wallet_balance = balance
            self.logger.debug(f"Wallet balance fetched: {balance}")
        except Exception as e:
            self.logger.error("Error fetching wallet balance", {"error": str(e)})
            self.wallet_balance = 0.0

    def set_trading_balance(self, amount: float):
        try:
            self.trading_balance = float(amount)
            self.logger.debug(f"Trading balance set: {self.trading_balance}")
        except Exception as e:
            self.logger.error("Error setting trading balance", {"error": str(e)})
            self.trading_balance = 0.0

    def get_ratio(self) -> float:
        if self.master_balance <= 0:
            return 0.0
        return self.trading_balance / self.master_balance

    def validate_trading_balance(self, amount: float) -> bool:
        return float(amount) <= self.wallet_balance