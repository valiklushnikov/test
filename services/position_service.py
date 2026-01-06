class PositionService:
    def __init__(self, logger):
        self.logger = logger
        self.positions = []
        self.open_orders = []
        self.bybit = None

    def set_bybit(self, bybit):
        self.bybit = bybit

    def fetch_positions(self):
        if not self.bybit:
            return
        self.positions = self.bybit.get_positions()

    def fetch_open_orders(self):
        if not self.bybit:
            return
        self.open_orders = self.bybit.get_open_orders()

    def get_position(self, symbol: str, side: str):
        for p in self.positions:
            if p.get("symbol") == symbol and p.get("side") == side:
                return p
        return None

    def calculate_pnl(self, position, current_price: float) -> float:
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
