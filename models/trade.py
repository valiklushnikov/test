from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    id: int
    master_trade_id: int
    server_trade_id: int
    symbol: str
    side: str
    entry_qty: float
    entry_price: float
    exit_qty: float
    exit_price: float
    pnl: float
    status: str
    opened_at: datetime
    closed_at: datetime
