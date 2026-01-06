from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed


class PriceService:
    def __init__(self, logger):
        self.logger = logger
        self.prices: Dict[str, float] = {}
        self.symbols: List[str] = []
        self.pairs: Dict[str, Dict] = {}
        self.bybit = None
        self._executor = ThreadPoolExecutor(max_workers=5)

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
        """Параллельная загрузка цен для всех символов"""
        if not self.symbols or not self.bybit:
            return

        # Если символов мало (<=3), загружаем последовательно
        if len(self.symbols) <= 3:
            data = self.bybit.get_tickers(self.symbols)
            if data:
                self.prices.update(data)
            return

        # Если символов много - параллельно
        try:
            futures = {
                self._executor.submit(self._fetch_single_price, symbol): symbol
                for symbol in self.symbols
            }

            updated_count = 0
            for future in as_completed(futures):
                try:
                    symbol, price = future.result()
                    if price > 0:
                        self.prices[symbol] = price
                        updated_count += 1
                except Exception:
                    pass

            if updated_count > 0:
                self.logger.info("Обновление цен по Bybit", {"symbols": updated_count})

        except Exception as e:
            self.logger.warning("Ошибка параллельной загрузки цен", {"error": str(e)})
            # Fallback на последовательную загрузку
            data = self.bybit.get_tickers(self.symbols)
            if data:
                self.prices.update(data)

    def _fetch_single_price(self, symbol: str) -> tuple:
        """Загрузка цены для одного символа"""
        try:
            ticker = self.bybit.get_ticker(symbol)
            price = ticker.get("price", 0.0)
            return symbol, price
        except Exception:
            return symbol, 0.0

    def get_price(self, symbol: str) -> float:
        return float(self.prices.get(symbol, 0.0))

    def get_all_prices(self) -> Dict[str, float]:
        return dict(self.prices)

    def shutdown(self):
        """Закрытие executor при остановке приложения"""
        self._executor.shutdown(wait=False)