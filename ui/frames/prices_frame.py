from tkinter import ttk


class PricesFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        # Treeview без лишних элементов
        self.tree = ttk.Treeview(self, columns=("symbol", "price"), show="headings", height=12)
        self.tree.heading("symbol", text="Символ")
        self.tree.heading("price", text="Цена")
        self.tree.column("symbol", width=140, anchor="w", stretch=True)
        self.tree.column("price", width=100, anchor="e", stretch=True)
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")
        self.bind("<Configure>", self._on_resize)

    def update_prices(self, data: dict):
        # Обновление без мерцания: только изменённые строки
        items = {self.tree.item(i, "values")[0]: i for i in self.tree.get_children()}
        for symbol, price in data.items():
            values = (symbol, f"{price:,.2f}")
            if symbol in items:
                self.tree.item(items[symbol], values=values)
            else:
                self.tree.insert("", "end", values=values)
        # Удалить лишние
        symbols = set(data.keys())
        for i in list(items.values()):
            if self.tree.item(i, "values")[0] not in symbols:
                self.tree.delete(i)

    def _on_resize(self, e):
        try:
            total = max(e.width - 20, 200)
            sym_w = int(total * 0.6)
            price_w = total - sym_w
            self.tree.column("symbol", width=sym_w)
            self.tree.column("price", width=price_w)
        except Exception:
            pass