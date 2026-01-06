import time


class SymbolRepository:
    def __init__(self, db):
        self.db = db

    def save_symbols(self, symbols_data: dict):
        """
        Сохраняет или обновляет символы в БД.
        symbols_data: dict, где ключ - symbol, значение - dict с параметрами
        """
        ts = int(time.time() * 1000)
        queries = []
        for symbol, data in symbols_data.items():
            # Map API keys to DB keys
            # API returns: min_order_qty, qty_step, min_notional_value
            min_qty = float(data.get("min_order_qty", 0))
            step_size = float(data.get("qty_step", 0)) or float(data.get("step_size", 0))
            
            queries.append((
                "INSERT OR REPLACE INTO symbols (symbol, min_order_qty, min_price, tick_size, step_size, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    symbol,
                    min_qty,
                    float(data.get("min_price", 0)),
                    float(data.get("tick_size", 0)),
                    step_size,
                    1 if data.get("status", True) else 0,
                    ts
                )
            ))
        
        # Выполняем транзакцию
        for sql, params in queries:
            self.db.execute(sql, params)

    def get_active_symbols_data(self):
        """
        Возвращает полные данные только для активных символов.
        """
        rows = self.db.fetchall("SELECT * FROM symbols WHERE status = 1")
        result = {}
        for r in rows:
            result[r["symbol"]] = {
                "min_order_qty": r["min_order_qty"],
                "min_price": r["min_price"],
                "tick_size": r["tick_size"],
                "step_size": r["step_size"],
                "status": bool(r["status"])
            }
        return result

    def get_all_symbols_data(self):
        """
        Возвращает полные данные по всем символам.
        """
        rows = self.db.fetchall("SELECT * FROM symbols")
        result = {}
        for r in rows:
            result[r["symbol"]] = {
                "min_order_qty": r["min_order_qty"],
                "min_price": r["min_price"],
                "tick_size": r["tick_size"],
                "step_size": r["step_size"],
                "status": bool(r["status"])
            }
        return result
