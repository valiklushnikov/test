class PositionRow:
    def __init__(self, symbol: str, side: str, size: float, avg_price: float, pnl: float):
        self.symbol = symbol
        self.side = side
        self.size = size
        self.avg_price = avg_price
        self.pnl = pnl
