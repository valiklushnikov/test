from typing import Dict, List
import requests


class BybitAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None
        self.last_error = None

    def connect(self):
        try:
            from pybit.unified_trading import HTTP
            # Use testnet=False explicitly to ensure mainnet
            self.session = HTTP(
                testnet=True,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=10000,  # Increase recv_window to avoid timestamp errors
            )
        except Exception as e:
            self.session = None
            self.last_error = f"Init Error: {str(e)}"

    def test_connection(self) -> bool:
        self.last_error = None
        if not self.session:
            self.last_error = "Session not initialized"
            return False
        try:
            # Force a request that requires authentication and correct permissions
            # get_api_key_information works for V5
            self.session.get_api_key_information()
            return True
        except Exception as e:
            # Store the exact error from the library
            self.last_error = str(e)
            return False

    def get_balance(self) -> float:
        if not self.session:
            return 0.0
        try:
            data = self.session.get_wallet_balance(accountType="UNIFIED")
            # Simplified extraction
            if isinstance(data, dict):
                list_data = data.get("result", {}).get("list", [])
                if list_data:
                    total = list_data[0].get("totalEquity")
                    return float(total or 0.0)
        except Exception:
            pass
        return 0.0

    def get_positions(self, symbol: str | None = None) -> List[Dict]:
        if not self.session:
            return []
        try:
            res = self.session.get_positions(category="linear",
                                             symbol=symbol) if symbol else self.session.get_positions(category="linear")
            items = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
            return items
        except Exception:
            return []

    def get_open_orders(self, symbol: str | None = None) -> List[Dict]:
        if not self.session:
            print("DEBUG: Session not initialized")
            return []
        try:
            # Если символ не указан, получаем все ордера по USDT
            if symbol:
                res = self.session.get_open_orders(category="linear", symbol=symbol)
            else:
                res = self.session.get_open_orders(category="linear", settleCoin="USDT")

            # print(f"DEBUG: Bybit API response: {res}")  # ← Отладка

            items = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
            # print(f"DEBUG: Extracted {len(items)} orders from response")  # ← Отладка

            # Выводим детали каждого ордера
            # for i, order in enumerate(items):
            #     print(f"DEBUG: Order {i}: {order.get('symbol')} {order.get('orderId')} {order.get('orderStatus')}")

            return items
        except Exception as e:
            # Логируем ошибку для отладки
            print(f"DEBUG: Exception in get_open_orders: {e}")
            return []

    def get_order_history(self, symbol: str | None = None, limit: int = 50) -> List[Dict]:
        """
        Получить историю ордеров (включая исполненные)

        Args:
            symbol: Символ для фильтрации
            limit: Количество записей (макс 50)
        """
        if not self.session:
            return []
        try:
            params = {
                "category": "linear",
                "limit": limit,
                "orderStatus": "Filled"
            }

            if symbol:
                params["symbol"] = symbol
            else:
                params["settleCoin"] = "USDT"

            res = self.session.get_order_history(**params)

            # print(f"DEBUG: Order history response: {res}")

            items = res.get("result", {}).get("list", []) if isinstance(res, dict) else []
            # print(f"DEBUG: Extracted {len(items)} filled orders from history")

            return items
        except Exception as e:
            print(f"DEBUG: Exception in get_order_history: {e}")
            return []

    def place_order(self, symbol: str, side: str, qty: float, order_type: str, price: float | None = None) -> str:
        if not self.session:
            return ""
        try:
            params = {"category": "linear", "symbol": symbol, "side": side, "orderType": order_type, "qty": str(qty)}
            if price is not None:
                params["price"] = str(price)

            # print(f"DEBUG: Placing order with params: {params}")  # ← Отладка

            res = self.session.place_order(**params)

            # print(f"DEBUG: Place order response: {res}")  # ← Отладка

            order_id = str(res.get("result", {}).get("orderId", ""))
            # print(f"DEBUG: Order placed with ID: {order_id}")  # ← Отладка

            return order_id
        except Exception as e:
            print(f"DEBUG: Exception placing order: {e}")  # ← Отладка
            return ""

    def place_conditional_order(self, symbol: str, side: str, qty: float, order_type: str, trigger_price: float,
                                price: float | None = None) -> str:
        if not self.session:
            return ""
        try:
            params = {"category": "linear", "symbol": symbol, "side": side, "orderType": order_type, "qty": str(qty),
                      "triggerPrice": str(trigger_price)}
            if price is not None:
                params["price"] = str(price)
            res = self.session.place_order(**params)
            return str(res.get("result", {}).get("orderId", ""))
        except Exception:
            return ""

    def cancel_order(self, symbol: str, order_id: str) -> bool:
        if not self.session:
            return False
        try:
            res = self.session.cancel_order(category="linear", symbol=symbol, orderId=order_id)
            return bool(res.get("retCode", 0) == 0)
        except Exception:
            return False

    def cancel_all_orders(self, symbol: str) -> bool:
        if not self.session:
            return False
        try:
            self.session.cancel_all_orders(category="linear", symbol=symbol)
            return True
        except Exception:
            return False

    def get_ticker(self, symbol: str) -> Dict:
        # Use session if available, otherwise fallback to public requests
        if self.session:
            try:
                res = self.session.get_tickers(category="linear", symbol=symbol)
                items = res.get("result", {}).get("list", [])
                price = float(items[0].get("lastPrice", 0.0)) if items else 0.0
                return {"symbol": symbol, "price": price}
            except Exception:
                # If session call fails, fall through to requests
                pass

        try:
            r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category": "linear", "symbol": symbol},
                             timeout=5)
            j = r.json() if r.content else {}
            items = j.get("result", {}).get("list", [])
            price = float(items[0].get("lastPrice", 0.0)) if items else 0.0
            return {"symbol": symbol, "price": price}
        except Exception:
            return {"symbol": symbol, "price": 0.0}

    def get_tickers(self, symbols: List[str]) -> Dict[str, float]:
        out = {}
        for s in symbols:
            out[s] = self.get_ticker(s)["price"]
        return out