class TradeRepository:
    def __init__(self, db):
        self.db = db

    def insert_trade(self, master_trade_id: int, server_trade_id: int, symbol: str, side: str, entry_qty: float, entry_price: float, status: str):
        self.db.execute(
            "INSERT INTO trades(master_trade_id, server_trade_id, symbol, side, entry_qty, entry_price, status, opened_at) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP)",
            (master_trade_id, server_trade_id, symbol, side, entry_qty, entry_price, status),
        )
