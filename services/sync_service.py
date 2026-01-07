from typing import Dict, List
from models.command import Command
from api.master_api import MasterAPI
from utils.helpers import timestamp_ms, round_step_size


class SyncService:
    def __init__(self, logger):
        self.logger = logger
        self.current_hash = ""
        self.executed_commands: Dict[str, bool] = {}

    def check_status(self, auth, app) -> bool:
        api_url = auth.settings.get("api_url", "")
        token = auth.get_token()

        if not api_url or not token:
            raise RuntimeError("API URL or token not configured")

        api = MasterAPI(api_url, token)
        data = api.get_status()

        # В v1.0, status возвращает только hash, без pairs
        new_hash = data.get("hash", "")
        changed = new_hash != self.current_hash

        if changed:
            self.current_hash = new_hash

        return changed

    def fetch_commands(self, auth) -> List[Command]:
        api = MasterAPI(auth.settings.get("api_url", ""), auth.get_token())
        data = api.get_orders()
        cmds = []
        for c in data.get("commands", []):
            cmds.append(Command(**c))
        return cmds

    def process_commands(self, commands: List[Command], app):
        for cmd in commands:
            if self.is_executed(cmd.id):
                continue
            
            try:
                app.logger.info("Processing command", {"id": cmd.id, "symbol": cmd.symbol, "side": cmd.position_side})
                received_at = timestamp_ms()
                
                # 1. Calculate Quantity
                # Get symbol settings from App (loaded from DB)
                symbol_data = app.symbol_repo.get_active_symbols_data().get(cmd.symbol, {})
                qty_step = float(symbol_data.get("step_size", 0.0))
                min_qty = float(symbol_data.get("min_order_qty", 0.0))
                
                # Calculate ratio
                ratio = 0.0
                try:
                    mb = float(app.balance_service.master_balance or 0.0)
                    tb = float(app.balance_service.trading_balance or 0.0)
                    if mb > 0:
                        ratio = tb / mb
                except Exception:
                    ratio = 0.0
                
                # Apply ratio
                raw_qty = float(cmd.trade_qty) * ratio if ratio > 0 else float(cmd.trade_qty)
                
                # Round to step size
                terminal_qty = round_step_size(raw_qty, qty_step)
                
                # Validation
                status = "skipped"
                result = {}
                error_message = None
                
                if terminal_qty < min_qty:
                    status = "skipped"
                    error_message = f"Qty {terminal_qty} below min {min_qty}"
                    app.logger.warning(error_message, {"id": cmd.id})
                    result = {"status": "skipped", "message": error_message}
                else:
                    # 2. Execute on Exchange
                    if hasattr(app, "trade_service"):
                        result = app.trade_service.execute_command(cmd, qty=terminal_qty)
                        status = result.get("status", "failed")
                        error_message = result.get("message")
                    else:
                        status = "failed"
                        error_message = "Trade service unavailable"

                executed_at = timestamp_ms()
                terminal_price = result.get("price", 0.0)
                terminal_fee = result.get("fee", 0.0)
                
                # 3. Send Log to Master
                log_payload = {
                    "order_id": cmd.id,
                    "symbol": cmd.symbol,
                    "action": "open" if cmd.position_side == "open" else "close",
                    "side": cmd.side,
                    "order_type": cmd.order_type,
                    "position_side": cmd.position_side,
                    "master_qty": cmd.trade_qty,
                    "master_price": cmd.trade_price,
                    "terminal_qty": terminal_qty if status == "success" else 0.0,
                    "terminal_price": terminal_price,
                    "terminal_fee": terminal_fee,
                    "status": status,
                    "error_message": error_message,
                    "exchange_order_id": result.get("exchange_order_id", ""),
                    "received_at_ms": received_at,
                    "executed_at_ms": executed_at,
                }
                
                api = MasterAPI(app.settings.get("api_url", ""), app.auth.get_token())
                try:
                    api.send_log(log_payload)
                except Exception as e:
                    app.logger.error("Failed to send log", {"error": str(e)})
                
                # 4. Handle Trade Lifecycle (Open/Close)
                if status == "success":
                    if cmd.position_side == "open":
                        # Register Open Trade
                        trade_payload = {
                            "symbol": cmd.symbol,
                            "side": cmd.side,
                            "entry_qty": terminal_qty,
                            "entry_price": terminal_price
                        }
                        try:
                            trade_resp = api.open_trade(trade_payload)
                            server_trade_id = trade_resp.get("trade_id")
                            if server_trade_id:
                                # Save to DB
                                app.db.execute(
                                    "INSERT INTO trades (server_trade_id, symbol, side, entry_qty, entry_price, status, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (server_trade_id, cmd.symbol, cmd.side, terminal_qty, terminal_price, "open", executed_at)
                                )
                                app.logger.info("Trade opened and saved", {"trade_id": server_trade_id})
                        except Exception as e:
                            app.logger.error("Failed to register open trade", {"error": str(e)})

                    elif cmd.position_side == "close":
                        # Close Trade
                        # Find open trade for this symbol (FIFO)
                        row = app.db.fetch_one("SELECT * FROM trades WHERE symbol = ? AND status = 'open' ORDER BY opened_at ASC LIMIT 1", (cmd.symbol,))
                        if row:
                            trade_id = row["server_trade_id"]
                            close_payload = {
                                "trade_id": trade_id,
                                "exit_qty": terminal_qty,
                                "exit_price": terminal_price,
                                "total_fee": terminal_fee
                            }
                            try:
                                api.close_trade(close_payload)
                                # Update DB
                                app.db.execute("UPDATE trades SET status = 'closed', closed_at = ?, exit_price = ?, exit_qty = ? WHERE id = ?", (executed_at, terminal_price, terminal_qty, row["id"]))
                                app.logger.info("Trade closed and updated", {"trade_id": trade_id})
                            except Exception as e:
                                app.logger.error("Failed to register close trade", {"error": str(e)})
                        else:
                            app.logger.warning("No open trade found to close in DB", {"symbol": cmd.symbol})

                self.mark_executed(cmd.id)
                
            except Exception as e:
                app.logger.error("Execute command error", {"id": cmd.id, "error": str(e)})

    def mark_executed(self, order_id: int):
        self.executed_commands[str(order_id)] = True

    def is_executed(self, order_id: int) -> bool:
        return self.executed_commands.get(str(order_id), False)
