from typing import List, Dict, Optional

class PositionService:
    def __init__(self, logger):
        self.logger = logger
        self.positions: List[Dict] = []
        self.bybit = None

    def set_bybit(self, bybit):
        self.bybit = bybit

    def fetch_positions(self, symbol: Optional[str] = None):
        if not self.bybit:
            self.logger.warning("Bybit API не инициализирован")
            return

        try:
            self.positions = self.bybit.get_positions(symbol)
            # Фильтруем только позиции с ненулевым размером
            self.positions = [p for p in self.positions if float(p.get("size", 0)) != 0]
            self.logger.debug(f"Загружено позиций: {len(self.positions)}",
                              {"symbol": symbol or "all"})
        except Exception as e:
            self.logger.error("Ошибка загрузки позиций", {"error": str(e)})
            self.positions = []

    def get_position(self, symbol: str, side: str) -> Optional[Dict]:
        for p in self.positions:
            if p.get("symbol") == symbol and p.get("side") == side:
                return p
        return None

    def get_positions_by_symbol(self, symbol: str) -> List[Dict]:
        """
        Получить все позиции по символу (и Long и Short)

        Args:
            symbol: Символ для фильтрации

        Returns:
            Список позиций по символу
        """
        return [p for p in self.positions if p.get("symbol") == symbol]

    def calculate_pnl(self, position: Optional[Dict], current_price: float) -> float:
        """
        Рассчитать PnL позиции

        Args:
            position: Данные позиции
            current_price: Текущая цена

        Returns:
            Нереализованный PnL
        """
        if not position:
            return 0.0

        size = float(position.get("size", 0.0))
        avg = float(position.get("avg_price", 0.0))

        if size <= 0 or avg <= 0:
            return 0.0

        side = position.get("side", "Buy")

        if side.lower() == "buy":
            return (current_price - avg) * size
        return (avg - current_price) * size

    def get_total_unrealized_pnl(self) -> float:
        """
        Получить суммарный нереализованный PnL по всем позициям

        Returns:
            Общий PnL
        """
        total = 0.0
        for p in self.positions:
            try:
                pnl = float(p.get("unrealisedPnl", 0.0))
                total += pnl
            except (ValueError, TypeError):
                continue
        return total

    def count_positions(self, symbol: Optional[str] = None) -> int:
        """
        Подсчитать количество позиций

        Args:
            symbol: Символ для фильтрации (если None - все позиции)

        Returns:
            Количество позиций
        """
        if symbol:
            return len(self.get_positions_by_symbol(symbol))
        return len(self.positions)

    def get_all_positions(self) -> List[Dict]:
        """Получить все открытые позиции"""
        return list(self.positions)
