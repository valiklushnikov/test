from dataclasses import dataclass
from datetime import datetime


@dataclass
class Order:
    order_id: str
    symbol: str
    side: str
    order_type: str
    qty: float
    price: float | None
    trigger_price: float | None
    status: str
    created_at: datetime
