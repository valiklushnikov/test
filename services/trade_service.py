from typing import Dict
from api.bybit_api import BybitAPI
from models.command import Command


class TradeService:
    def __init__(self, bybit: BybitAPI, logger):
        self.bybit = bybit
        self.logger = logger

    def execute_command(self, command: Command, qty: float | None = None) -> Dict:
        q = command.trade_qty if qty is None else qty
        oid = ""
        price = 0.0
        
        # Get current price for reference if needed
        ticker = self.bybit.get_ticker(command.symbol)
        current_price = ticker.get("price", 0.0)
        
        try:
            if command.order_type == "market":
                oid = self.open_position(command, q) if command.position_side == "open" else self.close_position(command, q)
                price = current_price
            elif command.order_type == "limit":
                oid = self.place_limit_order(command, q)
                price = command.trade_price or current_price
            elif command.order_type in ("stop_limit", "profit_limit"):
                oid = self.place_conditional_order(command, q)
                price = command.trade_price or current_price
            else:
                oid = ""
            
            if not oid:
                return {"status": "failed", "message": "Order not placed"}
                
            return {
                "status": "success", 
                "exchange_order_id": oid,
                "price": price,
                "fee": 0.0 # Fee is unknown at placement time
            }
        except Exception as e:
             self.logger.error("Trade execution error", {"error": str(e)})
             return {"status": "failed", "message": str(e)}

    def calculate_qty(self, master_qty: float) -> float:
        return master_qty

    def open_position(self, command: Command, qty: float | None = None) -> str:
        q = command.trade_qty if qty is None else qty
        return self.bybit.place_order(command.symbol, command.side, q, command.order_type, command.trade_price)

    def close_position(self, command: Command, qty: float | None = None) -> str:
        q = command.trade_qty if qty is None else qty
        return self.bybit.place_order(command.symbol, command.side, q, "market")

    def place_limit_order(self, command: Command, qty: float | None = None) -> str:
        q = command.trade_qty if qty is None else qty
        return self.bybit.place_order(command.symbol, command.side, q, "limit", command.trade_price)

    def place_conditional_order(self, command: Command, qty: float | None = None) -> str:
        q = command.trade_qty if qty is None else qty
        tp = command.trade_price or 0.0
        return self.bybit.place_conditional_order(command.symbol, command.side, q, "stop_limit", tp)

    def cancel_order(self, order_id: str):
        return True

    def send_execution_log(self, command: Command, result: Dict):
        self.logger.info("Execution log", {"id": command.id, "result": result})
