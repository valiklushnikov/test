class CommandRepository:
    def __init__(self, db):
        self.db = db

    def insert_executed(self, order_id: int, symbol: str, side: str, order_type: str, master_qty: float, terminal_qty: float, terminal_price: float, status: str, exchange_order_id: str):
        self.db.execute(
            "INSERT OR IGNORE INTO executed_commands(order_id, symbol, side, order_type, master_qty, terminal_qty, terminal_price, status, exchange_order_id, executed_at) VALUES(?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (order_id, symbol, side, order_type, master_qty, terminal_qty, terminal_price, status, exchange_order_id),
        )
