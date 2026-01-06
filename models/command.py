from dataclasses import dataclass


@dataclass
class Command:
    id: int
    symbol: str
    side: str
    position_side: str
    order_type: str
    trade_qty: float
    trade_price: float | None
    status: str
