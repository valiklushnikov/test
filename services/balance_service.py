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
            return
        self.wallet_balance = float(self.bybit.get_balance())

    def set_trading_balance(self, amount: float):
        self.trading_balance = float(amount)

    def get_ratio(self) -> float:
        if self.master_balance <= 0:
            return 0.0
        return self.trading_balance / self.master_balance

    def validate_trading_balance(self, amount: float) -> bool:
        return float(amount) <= self.wallet_balance
