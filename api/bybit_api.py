from typing import Dict, List
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import time


class BybitAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = None
        self.last_error = None
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._request_timeout = 10  # секунды
        self._retry_attempts = 2

    def connect(self):
        try:
            from pybit.unified_trading import HTTP
            self.session = HTTP(
                testnet=True,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=10000,
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
            self.session.get_api_key_information()
            return True
        except Exception as e:
            self.last_error = str(e)
            return False

    def get_balance(self) -> float:
        if not self.session:
            return 0.0
        try:
            def _fetch():
                data = self.session.get_wallet_balance(accountType="UNIFIED")
                if isinstance(data, dict):
                    list_data = data.get("result", {}).get("list", [])
                    if list_data:
                        total = list_data[0].get("totalEquity")
                        return float(total or 0.0)
                return 0.0

            return self._retry_request(_fetch)
        except Exception:
            return 0.0

    def get_positions(self, symbol: str | None = None) -> List[Dict]:
        if not self.session:
            return []
        try:
            def _fetch():
                if symbol:
                    res = self.session.get_positions(category="linear", symbol=symbol)
                else:
                    res = self.session.get_positions(category="linear")
                return res.get("result", {}).get("list", []) if isinstance(res, dict) else []

            return self._retry_request(_fetch)
        except Exception:
            return []

    def _retry_request(self, func, *args, **kwargs):
        """
        Выполняет запрос с повторными попытками при таймауте

        Args:
            func: Функция для выполнения
            *args, **kwargs: Параметры функции

        Returns:
            Результат функции или значение по умолчанию при ошибке
        """
        last_exception = None

        for attempt in range(self._retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                error_str = str(e)

                # Если это таймаут и есть еще попытки - ждем и пробуем снова
                if "timed out" in error_str.lower() or "timeout" in error_str.lower():
                    if attempt < self._retry_attempts - 1:
                        time.sleep(0.5)  # Небольшая задержка перед повтором
                        continue
                # Для других ошибок сразу выходим
                break

        # Если все попытки исчерпаны, выбрасываем последнее исключение
        if last_exception:
            raise last_exception

    def get_open_orders(self, symbol: str | None = None) -> List[Dict]:
        """Получение открытых ордеров с retry-логикой"""
        if not self.session:
            return []

        try:
            def _fetch():
                if symbol:
                    res = self.session.get_open_orders(category="linear", symbol=symbol)
                else:
                    res = self.session.get_open_orders(category="linear", settleCoin="USDT")
                return res.get("result", {}).get("list", []) if isinstance(res, dict) else []

            return self._retry_request(_fetch)

        except Exception as e:
            # Логируем только если это не таймаут (чтобы не спамить)
            if "timed out" not in str(e).lower():
                print(f"DEBUG: Exception in get_open_orders: {e}")
            return []

    def get_order_history(self, symbol: str | None = None, limit: int = 50) -> List[Dict]:
        """Получение истории ордеров с retry-логикой"""
        if not self.session:
            return []

        try:
            def _fetch():
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
                return res.get("result", {}).get("list", []) if isinstance(res, dict) else []

            return self._retry_request(_fetch)

        except Exception as e:
            if "timed out" not in str(e).lower():
                print(f"DEBUG: Exception in get_order_history: {e}")
            return []

    def get_orders_parallel(self) -> tuple:
        """
        Параллельная загрузка открытых и исполненных ордеров с обработкой таймаутов

        Returns:
            (open_orders, filled_orders)
        """
        if not self.session:
            return [], []

        try:
            # Запускаем два запроса параллельно с увеличенным таймаутом
            future_open = self._executor.submit(self.get_open_orders)
            future_history = self._executor.submit(self.get_order_history, None, 10)

            open_orders = []
            filled_orders = []

            # Ждём результаты с таймаутом
            try:
                open_orders = future_open.result(timeout=15)  # Увеличен таймаут
            except TimeoutError:
                # Если таймаут - просто возвращаем пустой список
                pass
            except Exception as e:
                if "timed out" not in str(e).lower():
                    print(f"DEBUG: Error fetching open orders: {e}")

            try:
                filled_orders = future_history.result(timeout=15)
            except TimeoutError:
                pass
            except Exception as e:
                if "timed out" not in str(e).lower():
                    print(f"DEBUG: Error fetching order history: {e}")

            return open_orders, filled_orders

        except Exception as e:
            if "timed out" not in str(e).lower():
                print(f"DEBUG: Exception in get_orders_parallel: {e}")
            return [], []

    def place_order(self, symbol: str, side: str, qty: float, order_type: str, price: float | None = None) -> str:
        if not self.session:
            return ""
        try:
            params = {"category": "linear", "symbol": symbol, "side": side, "orderType": order_type, "qty": str(qty)}
            if price is not None:
                params["price"] = str(price)

            res = self.session.place_order(**params)
            order_id = str(res.get("result", {}).get("orderId", ""))
            return order_id
        except Exception as e:
            print(f"DEBUG: Exception placing order: {e}")
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
        """Получение цены с retry-логикой"""
        if self.session:
            try:
                def _fetch():
                    res = self.session.get_tickers(category="linear", symbol=symbol)
                    items = res.get("result", {}).get("list", [])
                    price = float(items[0].get("lastPrice", 0.0)) if items else 0.0
                    return {"symbol": symbol, "price": price}

                return self._retry_request(_fetch)
            except Exception:
                pass

        # Fallback на публичный API
        try:
            r = requests.get("https://api.bybit.com/v5/market/tickers",
                             params={"category": "linear", "symbol": symbol},
                             timeout=5)
            j = r.json() if r.content else {}
            items = j.get("result", {}).get("list", [])
            price = float(items[0].get("lastPrice", 0.0)) if items else 0.0
            return {"symbol": symbol, "price": price}
        except Exception:
            return {"symbol": symbol, "price": 0.0}

    def get_tickers(self, symbols: List[str]) -> Dict[str, float]:
        """Batch загрузка цен с обработкой ошибок"""
        if not symbols:
            return {}

        # Если меньше 5 символов - batch запрос эффективнее
        if len(symbols) <= 5 and self.session:
            try:
                def _fetch():
                    res = self.session.get_tickers(category="linear")
                    items = res.get("result", {}).get("list", [])
                    out = {}
                    symbol_set = set(symbols)
                    for item in items:
                        sym = item.get("symbol")
                        if sym in symbol_set:
                            out[sym] = float(item.get("lastPrice", 0.0))
                    # Заполняем отсутствующие нулями
                    for s in symbols:
                        if s not in out:
                            out[s] = 0.0
                    return out

                return self._retry_request(_fetch)
            except Exception:
                pass

        # Fallback: параллельная загрузка для каждого символа
        out = {}
        futures = {self._executor.submit(self.get_ticker, s): s for s in symbols}
        for future in as_completed(futures, timeout=15):
            try:
                result = future.result(timeout=3)
                out[result["symbol"]] = result["price"]
            except Exception:
                symbol = futures[future]
                out[symbol] = 0.0

        return out

    def shutdown(self):
        """Закрытие executor"""
        self._executor.shutdown(wait=False)