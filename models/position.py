from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    side: str
    size: float
    avg_price: float
    mark_price: float
    unrealised_pnl: float
    leverage: int
