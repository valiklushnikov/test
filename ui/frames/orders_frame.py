from tkinter import ttk
from datetime import datetime


class OrdersFrame(ttk.Frame):
    """Фрейм для отображения открытых и недавно исполненных ордеров"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Создаем Treeview
        columns = ("time", "symbol", "side", "type", "qty", "price", "status")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=12
        )

        # Настройка заголовков
        headers = {
            "time": "Время",
            "symbol": "Символ",
            "side": "Сторона",
            "type": "Тип",
            "qty": "Количество",
            "price": "Цена",
            "status": "Статус"
        }

        for col, header in headers.items():
            self.tree.heading(col, text=header)

        # Настройка ширины колонок
        self.tree.column("time", width=80, anchor="w", stretch=True)
        self.tree.column("symbol", width=80, anchor="w", stretch=True)
        self.tree.column("side", width=50, anchor="center", stretch=True)
        self.tree.column("type", width=60, anchor="center", stretch=True)
        self.tree.column("qty", width=80, anchor="e", stretch=True)
        self.tree.column("price", width=90, anchor="e", stretch=True)
        self.tree.column("status", width=70, anchor="center", stretch=True)

        # Вертикальный скроллбар
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)

        # Layout
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

        # Тэги для раскраски
        self.tree.tag_configure("filled", foreground="green")
        self.tree.tag_configure("new", foreground="blue")
        self.tree.tag_configure("cancelled", foreground="red")

    def update(self, orders: list):
        """
        Обновить список ордеров

        Args:
            orders: Список ордеров от Bybit API (открытые + история)
        """
        print(f"DEBUG OrdersFrame: Updating with {len(orders)} orders")

        # Получаем существующие записи
        existing = {self.tree.item(i, "values")[0]: i for i in self.tree.get_children() if self.tree.item(i, "values")}

        processed_ids = set()

        for order in orders:
            order_id = order.get("orderId", "")
            if not order_id:
                continue

            # Извлекаем данные
            symbol = order.get("symbol", "")
            side = order.get("side", "")
            order_type = order.get("orderType", "")
            qty = float(order.get("qty", 0))

            # Цена исполнения для filled orders
            avg_price = float(order.get("avgPrice", 0))
            order_price = float(order.get("price", 0)) if order.get("price") else 0
            display_price = avg_price if avg_price > 0 else order_price

            status = order.get("orderStatus", "")

            # Время создания/обновления
            timestamp = int(order.get("updatedTime", order.get("createdTime", 0)))
            if timestamp > 0:
                time_str = datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
            else:
                time_str = "-"

            print(f"DEBUG OrdersFrame: Processing order {order_id}: {symbol} {side} {status}")

            # Форматируем значения
            values = (
                time_str,
                symbol,
                side,
                order_type,
                f"{qty:.4f}",
                f"{display_price:.2f}" if display_price > 0 else "Market",
                status
            )

            # Определяем тэг для раскраски
            tag = ""
            if status == "Filled":
                tag = "filled"
            elif status in ("New", "PartiallyFilled"):
                tag = "new"
            elif status == "Cancelled":
                tag = "cancelled"

            # Обновляем или создаем запись
            if order_id in existing:
                self.tree.item(existing[order_id], values=values, tags=(tag,))
            else:
                self.tree.insert("", 0, iid=order_id, values=values, tags=(tag,))  # Вставляем в начало

            processed_ids.add(order_id)

        # Удаляем ордера, которых больше нет (оставляем только последние 50)
        all_items = self.tree.get_children()
        if len(all_items) > 50:
            for item in all_items[50:]:
                self.tree.delete(item)

    def clear(self):
        """Очистить все ордера"""
        for item in self.tree.get_children():
            self.tree.delete(item)