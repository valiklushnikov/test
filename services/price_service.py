from typing import Dict, List


class PriceService:
    def __init__(self, logger):
        self.logger = logger
        self.prices: Dict[str, float] = {}
        self.symbols: List[str] = []
        self.pairs: Dict[str, Dict] = {}
        self.bybit = None

    def set_bybit(self, bybit):
        self.bybit = bybit

    def update_symbols(self, pairs):
        if isinstance(pairs, dict):
            self.pairs = dict(pairs)
            self.symbols = list(pairs.keys())
        else:
            self.symbols = list(pairs)
        for s in self.symbols:
            self.prices.setdefault(s, 0.0)

    def fetch_prices(self):
        if not self.symbols:
            return
        data = self.bybit.get_tickers(self.symbols) if self.bybit else {}
        if data:
            # self.logger.info("Обновление цен по Bybit", {"symbols": len(data)})
            self.prices.update(data)
        else:
            self.logger.warning("Не удалось получить цены", {})

    def get_price(self, symbol: str) -> float:
        return float(self.prices.get(symbol, 0.0))

    def get_all_prices(self) -> Dict[str, float]:
        return dict(self.prices)
