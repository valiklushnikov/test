from tkinter import ttk
from datetime import datetime


class OrdersFrame(ttk.Frame):
    """Фрейм для отображения открытых и недавно исполненных ордеров"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Создаем Treeview
        columns = ("id", "time", "symbol", "side", "type", "qty", "price", "status")
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=12
        )

        # Настройка заголовков
        headers = {
            "id": "ID",
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
        self.tree.column("id", width=100, anchor="w", stretch=True)
        self.tree.column("time", width=80, anchor="center", stretch=True)
        self.tree.column("symbol", width=70, anchor="center", stretch=True)
        self.tree.column("side", width=50, anchor="center", stretch=True)
        self.tree.column("type", width=50, anchor="center", stretch=True)
        self.tree.column("qty", width=70, anchor="e", stretch=True)
        self.tree.column("price", width=80, anchor="e", stretch=True)
        self.tree.column("status", width=60, anchor="center", stretch=True)

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
        existing_ids = set(self.tree.get_children())
        processed_ids = set()

        for order in orders:
            order_id = order.get("orderId")
            if not order_id:
                continue

            symbol = order.get("symbol", "")
            side = order.get("side", "")
            order_type = order.get("orderType", "")
            qty = float(order.get("qty", 0))

            avg_price = float(order.get("avgPrice") or 0)
            order_price = float(order.get("price") or 0)
            display_price = avg_price if avg_price > 0 else order_price

            status = order.get("orderStatus", "")

            timestamp = int(order.get("updatedTime") or order.get("createdTime") or 0)
            time_str = (
                datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
                if timestamp else "-"
            )

            values = (
                order_id[:18],
                time_str,
                symbol,
                side,
                order_type,
                f"{qty:.4f}",
                f"{display_price:.2f}" if display_price > 0 else "Market",
                status
            )

            tag = ""
            if status == "Filled":
                tag = "filled"
            elif status in ("New", "PartiallyFilled"):
                tag = "new"
            elif status == "Cancelled":
                tag = "cancelled"

            if order_id in existing_ids:
                self.tree.item(order_id, values=values, tags=(tag,))
            else:
                self.tree.insert("", 0, iid=order_id, values=values, tags=(tag,))

            processed_ids.add(order_id)

        # удаляем устаревшие
        for iid in existing_ids - processed_ids:
            self.tree.delete(iid)

        # лимит 50 строк
        for iid in self.tree.get_children()[50:]:
            self.tree.delete(iid)

    def clear(self):
        """Очистить все ордера"""
        for item in self.tree.get_children():
            self.tree.delete(item)