from typing import List, Dict, Optional


class OrderService:
    """Сервис для работы с открытыми ордерами"""

    def __init__(self, logger):
        self.logger = logger
        self.open_orders: List[Dict] = []
        self.order_history: List[Dict] = []  # ← История исполненных
        self.bybit = None

    def set_bybit(self, bybit):
        """Установка ссылки на Bybit API"""
        self.bybit = bybit

    def fetch_open_orders(self, symbol: Optional[str] = None):
        """
        Получить открытые ордера с биржи

        Args:
            symbol: Символ для фильтрации (если None - все ордера)
        """
        if not self.bybit:
            self.logger.warning("Bybit API не инициализирован")
            return

        try:
            self.open_orders = self.bybit.get_open_orders(symbol)
            print(f"DEBUG OrderService: Received {len(self.open_orders)} open orders")
            self.logger.debug(f"Загружено ордеров: {len(self.open_orders)}",
                              {"symbol": symbol or "all"})
        except Exception as e:
            self.logger.error("Ошибка загрузки ордеров", {"error": str(e)})
            self.open_orders = []

    def fetch_order_history(self, symbol: Optional[str] = None, limit: int = 20):
        """
        Получить историю исполненных ордеров

        Args:
            symbol: Символ для фильтрации
            limit: Количество записей
        """
        if not self.bybit:
            self.logger.warning("Bybit API не инициализирован")
            return

        try:
            self.order_history = self.bybit.get_order_history(symbol, limit)
            print(f"DEBUG OrderService: Received {len(self.order_history)} filled orders")
            self.logger.debug(f"Загружено исполненных ордеров: {len(self.order_history)}",
                              {"symbol": symbol or "all"})
        except Exception as e:
            self.logger.error("Ошибка загрузки истории ордеров", {"error": str(e)})
            self.order_history = []

    def get_all_orders_combined(self) -> List[Dict]:
        """
        Объединить открытые и недавно исполненные ордера

        Returns:
            Список всех ордеров
        """
        return self.open_orders + self.order_history

    def get_orders_by_symbol(self, symbol: str) -> List[Dict]:
        """
        Получить ордера по конкретному символу из кэша

        Args:
            symbol: Символ для фильтрации

        Returns:
            Список ордеров по символу
        """
        return [o for o in self.open_orders if o.get("symbol") == symbol]

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Найти ордер по ID

        Args:
            order_id: ID ордера

        Returns:
            Словарь с данными ордера или None
        """
        for order in self.open_orders:
            if order.get("orderId") == order_id:
                return order
        return None

    def count_orders(self, symbol: Optional[str] = None) -> int:
        """
        Подсчитать количество ордеров

        Args:
            symbol: Символ для фильтрации (если None - все ордера)

        Returns:
            Количество ордеров
        """
        if symbol:
            return len(self.get_orders_by_symbol(symbol))
        return len(self.open_orders)

    def get_all_orders(self) -> List[Dict]:
        """Получить все открытые ордера"""
        return list(self.open_orders)