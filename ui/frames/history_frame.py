from tkinter import ttk
from datetime import datetime
from config import HISTORY_ORDERS_LIMIT

class HistoryFrame(ttk.Frame):
    """Фрейм для отображения истории исполненных ордеров"""

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
        self.tree.column("id", width=80, anchor="center", stretch=True)
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
        self.tree.tag_configure("cancelled", foreground="red")
        self.tree.tag_configure("rejected", foreground="orange")

    def update(self, orders: list):
        """Обновить историю ордеров"""
        # Сортируем ордера по времени (новые первыми)
        sorted_orders = sorted(
            orders,
            key=lambda o: int(o.get("updatedTime") or o.get("createdTime") or 0),
            reverse=True
        )

        # Собираем данные для отображения
        orders_data = []
        for order in sorted_orders[:HISTORY_ORDERS_LIMIT]:  # Берем максимум 100 записей
            order_id = order.get("orderId")
            if not order_id:
                continue

            symbol = order.get("symbol", "")
            side = order.get("side", "")
            order_type = order.get("orderType", "")
            qty = float(order.get("qty", 0))

            # Для истории берем среднюю цену исполнения
            avg_price = float(order.get("avgPrice") or 0)
            order_price = float(order.get("price") or 0)
            display_price = avg_price if avg_price > 0 else order_price

            status = order.get("orderStatus", "")

            # Используем время обновления для истории
            timestamp = int(order.get("updatedTime") or order.get("createdTime") or 0)
            time_str = (
                datetime.fromtimestamp(timestamp / 1000).strftime("%H:%M:%S")
                if timestamp else "-"
            )

            values = (
                order_id[-8:],
                time_str,
                symbol,
                side,
                order_type,
                f"{qty:.4f}",
                f"{display_price:.2f}" if display_price > 0 else "Market",
                status
            )

            # Определяем тег по статусу
            tag = ""
            if status == "Filled":
                tag = "filled"
            elif status == "Cancelled":
                tag = "cancelled"
            elif status == "Rejected":
                tag = "rejected"

            orders_data.append((order_id, values, tag, timestamp))

        # Получаем текущие ID
        existing_ids = {self.tree.item(iid)["values"][0]: iid for iid in self.tree.get_children()}
        new_order_ids = {data[0][-8:] for data in orders_data}

        # Удаляем устаревшие записи
        for short_id, iid in list(existing_ids.items()):
            if short_id not in new_order_ids:
                self.tree.delete(iid)

        # Обновляем или добавляем записи
        # Очищаем дерево и заполняем заново в правильном порядке
        # Это предотвращает "прыжки" списка
        for item in self.tree.get_children():
            self.tree.delete(item)

        for order_id, values, tag, timestamp in orders_data:
            self.tree.insert("", "end", iid=order_id, values=values, tags=(tag,))

    def clear(self):
        """Очистить всю историю"""
        for item in self.tree.get_children():
            self.tree.delete(item)