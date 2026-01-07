import tkinter as tk
from tkinter import ttk
from utils.validators import is_valid_uuid, is_valid_url
from ui.windows.main_window import MainWindow
from ui.widgets.loading_indicator import LoadingIndicator


class LoginWindow:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self._center(500, 500)
        outer = ttk.Frame(root)
        outer.pack(fill="both", expand=True)
        frame = ttk.Frame(outer, padding=24)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(frame, text="API URL:").grid(row=0, column=0, sticky="w")
        self.url_var = tk.StringVar(value=self.app.settings.get("api_url", ""))
        self.url_entry = ttk.Entry(frame, textvariable=self.url_var, width=40)
        self.url_entry.grid(row=1, column=0, sticky="ew")
        ttk.Label(frame, text="Terminal UID:").grid(row=2, column=0, sticky="w")
        self.uid_var = tk.StringVar(value="")
        self.uid_entry = ttk.Entry(frame, textvariable=self.uid_var, show="*", width=40)
        self.uid_entry.grid(row=3, column=0, sticky="ew")
        self.status_var = tk.StringVar(value="Ожидание...")
        ttk.Button(frame, text="Войти", command=self.login).grid(row=4, column=0, pady=8, sticky="ew")
        ttk.Label(frame, textvariable=self.status_var).grid(row=5, column=0, sticky="w")
        frame.columnconfigure(0, weight=1)
        self._init_clipboard_support()
        self._init_context_menu()
        self.loading = LoadingIndicator(frame)

    def login(self):
        url = self.url_var.get().strip()
        uid = self.uid_var.get().strip()
        if not is_valid_url(url):
            self.status_var.set("Ошибка: некорректный URL")
            return
        if not is_valid_uuid(uid):
            self.status_var.set("Ошибка: некорректный UID")
            return
        try:
            token, info, pairs = self.app.auth.login(url, uid)
            self.app.update_symbols(pairs)
            try:
                self.app._update_prices()
            except Exception:
                pass
            try:
                self.app.balance_service.master_balance = float(info.get("balance", 0))
            except Exception:
                self.app.balance_service.master_balance = 0.0
            self.app.logger.info("Авторизация успешна", {"uid": uid})
            self.app.start()
            self.app.settings.set("api_url", url)
            self.status_var.set("Успешно")
            self.root.after(200, self._to_main)
        except Exception as e:
            self.app.logger.error("Авторизация ошибка", {"uid": uid, "error": str(e)})
            self.status_var.set(f"Ошибка: {e}")

    def _to_main(self):
        for w in list(self.root.winfo_children()):
            w.destroy()
        MainWindow(self.root, self.app)

    def _center(self, w, h):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _init_clipboard_support(self):
        # Удалены дублирующие биндинги
        pass

    def _on_paste(self, e):
        pass

    def _on_copy(self, e):
        pass

    def _on_cut(self, e):
        pass

    def _init_context_menu(self):
        self._ctx_widget = None
        self._menu = tk.Menu(self.root, tearoff=0)
        self._menu.add_command(label="Вставить", command=self._ctx_paste)
        self._menu.add_command(label="Копировать", command=self._ctx_copy)
        self._menu.add_command(label="Вырезать", command=self._ctx_cut)
        self.root.bind_all("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, e):
        self._ctx_widget = e.widget
        try:
            self._menu.tk_popup(e.x_root, e.y_root)
        finally:
            self._menu.grab_release()

    def _ctx_paste(self):
        if not self._ctx_widget:
            return
        try:
            text = self.root.clipboard_get()
            if hasattr(self._ctx_widget, "insert"):
                self._ctx_widget.insert("insert", text)
        except Exception:
            pass

    def _ctx_copy(self):
        w = self._ctx_widget
        if not w:
            return
        try:
            start = w.index("sel.first")
            end = w.index("sel.last")
            value = w.get()
            sel = value[start:end] if isinstance(value, str) else ""
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
        except Exception:
            pass

    def _ctx_cut(self):
        w = self._ctx_widget
        if not w:
            return
        try:
            start = w.index("sel.first")
            end = w.index("sel.last")
            value = w.get()
            sel = value[start:end] if isinstance(value, str) else ""
            if sel:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
                w.delete(start, end)
        except Exception:
            pass
