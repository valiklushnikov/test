from tkinter import ttk


class PositionsFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        # Treeview без лишних элементов
        self.tree = ttk.Treeview(self, columns=("symbol", "side", "size", "avg", "pnl"), show="headings", height=12)
        for c, n in zip(("symbol", "side", "size", "avg", "pnl"), ("Символ", "Сторона", "Размер", "Средн.", "PnL")):
            self.tree.heading(c, text=n)
        self.tree.column("symbol", width=140, anchor="w", stretch=True)
        self.tree.column("side", width=80, anchor="center", stretch=True)
        self.tree.column("size", width=100, anchor="e", stretch=True)
        self.tree.column("avg", width=120, anchor="e", stretch=True)
        self.tree.column("pnl", width=120, anchor="e", stretch=True)
        vs = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vs.pack(side="right", fill="y")

    def update(self, positions: list):
        # Обновление без мерцания: только изменённые строки
        items = {self.tree.item(i, "values")[0]: i for i in self.tree.get_children()}
        for p in positions:
            symbol = p.get("symbol", "")
            values = (symbol, p.get("side", ""), p.get("size", 0), p.get("avg_price", 0), p.get("unrealised_pnl", 0))
            if symbol in items:
                self.tree.item(items[symbol], values=values)
            else:
                self.tree.insert("", "end", values=values)
        # Удалить лишние
        symbols = {p.get("symbol") for p in positions}
        for i in list(items.values()):
            if self.tree.item(i, "values")[0] not in symbols:
                self.tree.delete(i)