from typing import Dict
from services.price_service import PriceService
from services.balance_service import BalanceService
from services.position_service import PositionService
from services.order_service import OrderService
from services.history_service import HistoryService
from services.sync_service import SyncService
from utils.helpers import timestamp_ms
from utils.async_executor import AsyncExecutor
from api.bybit_api import BybitAPI
from config import (
    PRICE_UPDATE_INTERVAL,
    BALANCE_UPDATE_INTERVAL,
    ORDERS_UPDATE_INTERVAL,
    POLLING_INTERVAL,
    TOKEN_REFRESH_INTERVAL,
    HISTORY_UPDATE_INTERVAL,
    HISTORY_ORDERS_LIMIT
)


class App:
    def __init__(self, auth, events, scheduler, settings, logger, db):
        self.auth = auth
        self.events = events
        self.scheduler = scheduler
        self.settings = settings
        self.logger = logger
        self.db = db

        # Async executor для параллельных операций
        self.executor = AsyncExecutor(max_workers=10)

        # Инициализация репозиториев
        from database.repositories.symbol_repository import SymbolRepository
        self.symbol_repo = SymbolRepository(db)

        # Инициализация сервисов
        self.price_service = PriceService(logger)
        self.balance_service = BalanceService(logger)
        self.position_service = PositionService(logger)
        self.order_service = OrderService(logger)
        self.history_service = HistoryService(logger)
        self.sync_service = SyncService(logger)

        # Bybit API
        self.bybit = BybitAPI("", "")
        self.price_service.set_bybit(self.bybit)
        self.balance_service.set_bybit(self.bybit)
        self.position_service.set_bybit(self.bybit)
        self.order_service.set_bybit(self.bybit)
        self.history_service.set_bybit(self.bybit)

        # Загружаем символы из БД
        self._load_symbols_from_db()

        # Статусы подключения
        self.connected_api = False
        self.connected_bybit = False
        self.started = False

        # Trade Service
        from services.trade_service import TradeService
        self.trade_service = TradeService(self.bybit, logger)

    def _load_symbols_from_db(self):
        try:
            symbols_data = self.symbol_repo.get_active_symbols_data()
            if symbols_data:
                self.price_service.update_symbols(symbols_data)
                self.logger.info(f"Loaded {len(symbols_data)} symbols from DB")
        except Exception as e:
            self.logger.error("Failed to load symbols from DB", {"error": str(e)})

    def start(self):
        if self.started:
            return
        self._schedule_tasks()
        self.started = True
        self.events.emit("on_connected", {"ts": timestamp_ms()})

    def stop(self):
        self.scheduler.stop()
        self.executor.shutdown()
        self.started = False
        self.events.emit("on_disconnected", {"ts": timestamp_ms()})

    def _schedule_tasks(self):
        # Сразу обновляем токен и пары при старте
        self._refresh_token()
        self.scheduler.add_task("poll_status", POLLING_INTERVAL, self._poll_status)
        self.scheduler.add_task("update_prices", PRICE_UPDATE_INTERVAL, self._update_prices)
        self.scheduler.add_task("update_balance", BALANCE_UPDATE_INTERVAL, self._update_balance)
        self.scheduler.add_task("update_orders", ORDERS_UPDATE_INTERVAL, self._update_orders)
        self.scheduler.add_task("update_history", HISTORY_UPDATE_INTERVAL, self._update_history)
        self.scheduler.add_task("refresh_token", TOKEN_REFRESH_INTERVAL, self._refresh_token)
        self.scheduler.start()

    def _poll_status(self):
        try:
            changed = self.sync_service.check_status(self.auth, self)
            if not self.connected_api:
                self.connected_api = True
                self.events.emit("on_api_status", {"status": True})
            if changed:
                commands = self.sync_service.fetch_commands(self.auth)
                self.sync_service.process_commands(commands, self)
                self.events.emit("on_command_received", {"count": len(commands)})
        except Exception as e:
            self.connected_api = False
            self.events.emit("on_api_status", {"status": False})
            error_str = str(e)
            if "WinError 10061" in error_str or "Connection refused" in error_str:
                self.logger.error("Сервер API недоступен")
            else:
                self.logger.error("API polling error", {"error": error_str})

    def _update_prices(self):
        if not self.connected_bybit:
            return
        try:
            self.price_service.fetch_prices()
            self.events.emit("on_price_updated", self.price_service.get_all_prices())
        except Exception as e:
            self.logger.error("Update prices error", {"error": str(e)})

    def _update_balance(self):
        """Обновление баланса и позиций (параллельно)"""
        if not self.connected_bybit:
            return

        try:
            # Сначала устанавливаем trading balance (быстрая операция)
            try:
                tb = float(self.settings.get("trading_balance", "0"))
                self.balance_service.set_trading_balance(tb)
            except Exception as e:
                self.logger.error("Failed to set trading balance", {"error": str(e)})

            # Параллельное выполнение двух операций (balance и positions)
            tasks = {
                'balance': lambda: self.balance_service.fetch_wallet_balance(),
                'positions': lambda: self.position_service.fetch_positions()
            }

            # Выполняем параллельно
            try:
                self.executor.run_parallel(tasks)
            except Exception as e:
                self.logger.error("Parallel execution error", {"error": str(e)})

            # Эмитим события даже если были ошибки (покажем последние известные данные)
            try:
                self.events.emit("on_positions_updated", self.position_service.positions)
            except Exception as e:
                self.logger.error("Failed to emit positions", {"error": str(e)})

            try:
                self.events.emit("on_balance_updated", {
                    "wallet": self.balance_service.wallet_balance,
                    "trading": self.balance_service.trading_balance
                })
            except Exception as e:
                self.logger.error("Failed to emit balance", {"error": str(e)})

        except Exception as e:
            error_str = str(e)
            # Не логируем таймауты как серьезные ошибки
            if "timed out" not in error_str.lower() and "timeout" not in error_str.lower():
                self.logger.error("Update balance error", {"error": error_str})

    def _update_orders(self):
        """Обновление ТОЛЬКО открытых ордеров"""
        if not self.connected_bybit:
            return
        try:
            # Получаем только открытые ордера
            self.order_service.fetch_open_orders()

            # Отправляем только открытые ордера
            open_orders = self.order_service.get_all_orders()
            self.events.emit("on_orders_updated", open_orders)
        except Exception as e:
            self.logger.error("Update orders error", {"error": str(e)})

    def _update_history(self):
        """Обновление истории ордеров (с интервалом 60с)"""
        if not self.connected_bybit:
            return
        try:
            # Получаем историю исполненных ордеров
            self.history_service.fetch_orders_history(symbol=None, limit=HISTORY_ORDERS_LIMIT)

            # Отправляем историю
            history = self.history_service.get_all_orders_history()
            self.events.emit("on_history_updated", history)
        except Exception as e:
            self.logger.error("Update history error", {"error": str(e)})

    def _refresh_token(self):
        try:
            token = self.auth.refresh_token()
            if token:
                self.settings.set("token", token)
                self.settings.save()
                self.logger.info("Token refreshed successfully")
            pairs = self.auth.get_pairs()
            if pairs:
                self.update_symbols(pairs)
        except Exception as e:
            self.logger.error("Token refresh error", {"error": str(e)})

    def update_symbols(self, pairs: Dict[str, dict]):
        """Обновляет символы в БД и в сервисе цен"""
        try:
            self.symbol_repo.save_symbols(pairs)
            active_symbols = self.symbol_repo.get_active_symbols_data()
            self.price_service.update_symbols(active_symbols)
        except Exception as e:
            self.logger.error("Failed to update symbols", {"error": str(e)})

    def configure_bybit(self):
        key = self.settings.get("bybit_api_key", "")
        secret = self.settings.get("bybit_api_secret", "")

        if not key or not secret:
            self.connected_bybit = False
            self.events.emit("on_bybit_status", {"status": False})
            return

        self.bybit = BybitAPI(key, secret)
        self.bybit.connect()
        self.connected_bybit = self.bybit.test_connection()

        self.events.emit("on_bybit_status", {"status": self.connected_bybit})

        # Обновляем ссылки на API во всех сервисах
        self.price_service.set_bybit(self.bybit)
        self.balance_service.set_bybit(self.bybit)
        self.position_service.set_bybit(self.bybit)
        self.order_service.set_bybit(self.bybit)
        self.history_service.set_bybit(self.bybit)

        from services.trade_service import TradeService
        self.trade_service = TradeService(self.bybit, self.logger)

        if self.connected_bybit:
            self.logger.info("Bybit connected successfully")
            # Параллельная первая загрузка данных
            self._initial_data_load()
        else:
            self.logger.warning(f"Bybit connection failed: {self.bybit.last_error}")

    def _initial_data_load(self):
        """Параллельная загрузка всех данных при подключении"""
        if not self.connected_bybit:
            return

        try:
            # Сначала синхронно загружаем баланс для корректной инициализации
            self.balance_service.fetch_wallet_balance()
            tb = float(self.settings.get("trading_balance", "0"))
            self.balance_service.set_trading_balance(tb)

            # Эмитим начальные значения баланса
            self.events.emit("on_balance_updated", {
                "wallet": self.balance_service.wallet_balance,
                "trading": self.balance_service.trading_balance
            })

            # Затем параллельно загружаем остальное
            tasks = {
                'prices': lambda: self._update_prices(),
                'orders': lambda: self._update_orders(),
                'positions': lambda: self.position_service.fetch_positions(),
                'history': lambda: self.history_service.fetch_orders_history()
            }
            self.executor.run_parallel(tasks)

            # Обновляем позиции
            self.events.emit("on_positions_updated", self.position_service.positions)
            self.events.emit("on_history_updated", self.history_service.get_all_orders_history())

        except Exception as e:
            self.logger.error("Initial data load error", {"error": str(e)})