import tkinter as tk
from tkinter import ttk
from utils.validators import is_valid_api_key
import requests
import threading


class SettingsWindow:
    instance = None

    def __init__(self, root, app):
        if SettingsWindow.instance:
            try:
                SettingsWindow.instance.top.deiconify()
                SettingsWindow.instance.top.lift()
                SettingsWindow.instance.top.focus_force()
                return
            except Exception:
                SettingsWindow.instance = None
        self.app = app
        self.top = tk.Toplevel(root)
        self.top.title("Настройки")
        self.top.geometry("500x500") # Increased height for IP
        self.top.resizable(False, False)
        SettingsWindow.instance = self
        frame = ttk.Frame(self.top, padding=12)
        frame.pack(fill="both", expand=True)
        
        # IP Address Section
        ip_frame = ttk.Frame(frame)
        ip_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(ip_frame, text="Ваш IP адрес:").pack(side="left")
        self.ip_var = tk.StringVar(value="Загрузка...")
        ttk.Entry(ip_frame, textvariable=self.ip_var, state="readonly", width=16).pack(side="left", padx=5)
        ttk.Button(ip_frame, text="Копировать", command=self.copy_ip).pack(side="left")
        
        ttk.Label(frame, text="API URL:").grid(row=1, column=0, sticky="w")
        self.api_url = tk.StringVar(value=self.app.settings.get("api_url", ""))
        api_entry = ttk.Entry(frame, textvariable=self.api_url, width=40)
        api_entry.state(["disabled"])
        api_entry.grid(row=2, column=0, sticky="ew")
        ttk.Separator(frame).grid(row=3, column=0, sticky="ew", pady=8)
        ttk.Label(frame, text="Bybit API Key:").grid(row=4, column=0, sticky="w")
        self.bybit_key = tk.StringVar(value=self.app.settings.get("bybit_api_key", ""))
        ttk.Entry(frame, textvariable=self.bybit_key, show="*", width=40).grid(row=5, column=0, sticky="ew")
        ttk.Label(frame, text="Bybit API Secret:").grid(row=6, column=0, sticky="w")
        self.bybit_secret = tk.StringVar(value=self.app.settings.get("bybit_api_secret", ""))
        ttk.Entry(frame, textvariable=self.bybit_secret, show="*", width=40).grid(row=7, column=0, sticky="ew")
        ttk.Button(frame, text="Проверить подключение", command=self.test_connection).grid(row=8, column=0, sticky="ew", pady=4)
        # Status label removed as requested
        # self.status_var = tk.StringVar(value="Статус: ● Отключено")
        # ttk.Label(frame, textvariable=self.status_var).grid(row=9, column=0, sticky="w")
        ttk.Separator(frame).grid(row=10, column=0, sticky="ew", pady=8)
        ttk.Label(frame, text="Баланс кошелька:").grid(row=11, column=0, sticky="w")
        self.wallet_balance = tk.StringVar(value=f"{self.app.balance_service.wallet_balance:.2f}")
        ttk.Label(frame, textvariable=self.wallet_balance).grid(row=12, column=0, sticky="w")
        ttk.Label(frame, text="Торговый баланс:").grid(row=13, column=0, sticky="w")
        self.trading_balance = tk.StringVar(value=str(self.app.settings.get("trading_balance", "0")))
        ttk.Entry(frame, textvariable=self.trading_balance, width=20).grid(row=14, column=0, sticky="w")
        ttk.Button(frame, text="Сохранить", command=self.save).grid(row=15, column=0, sticky="ew", pady=8)
        actions = ttk.Frame(frame)
        actions.grid(row=16, column=0, sticky="ew")
        ttk.Button(actions, text="Выход из аккаунта", command=self.logout).pack(side="left")
        frame.columnconfigure(0, weight=1)
        
        # Start fetching IP in background
        threading.Thread(target=self._fetch_ip, daemon=True).start()

    def _fetch_ip(self):
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            if r.status_code == 200:
                ip = r.json().get("ip", "Не удалось определить")
                self.top.after(0, lambda: self.ip_var.set(ip))
            else:
                self.top.after(0, lambda: self.ip_var.set("Ошибка получения"))
        except Exception:
            self.top.after(0, lambda: self.ip_var.set("Ошибка сети"))

    def copy_ip(self):
        ip = self.ip_var.get()
        if ip and "..." not in ip and "Ошибка" not in ip:
            self.top.clipboard_clear()
            self.top.clipboard_append(ip)
            self.top.update() # Required for clipboard to work

    def test_connection(self):
        key = self.bybit_key.get().strip()
        secret = self.bybit_secret.get().strip()
        from tkinter import messagebox
        
        if not is_valid_api_key(key) or not is_valid_api_key(secret):
            # self.status_var.set("Статус: Ошибка ключей")
            messagebox.showerror("Ошибка", "API ключи имеют неверный формат.")
            return

        # 1. Update settings locally for the app
        self.app.settings.set("bybit_api_key", key, secure=True)
        self.app.settings.set("bybit_api_secret", secret, secure=True)
        
        # 2. Re-initialize the BybitAPI instance with new keys
        # This calls BybitAPI(key, secret) which does basic init but NO network call yet
        self.app.configure_bybit()
        
        # 3. Explicitly call connect() which initializes the session
        # (configure_bybit already calls connect(), but let's be sure logic is clear)
        # 4. Run test_connection() which performs the actual network request
        ok = self.app.bybit.test_connection()
        
        if ok:
            # self.status_var.set("Статус: ● Подключено")
            self.app.balance_service.fetch_wallet_balance()
            self.wallet_balance.set(f"{self.app.balance_service.wallet_balance:.2f}")
            messagebox.showinfo("Успех", "Подключение к Bybit установлено успешно!")
        else:
            # self.status_var.set("Статус: ● Отключено")
            error_msg = self.app.bybit.last_error or "Неизвестная ошибка"
            messagebox.showerror("Ошибка подключения", 
                f"Не удалось подключиться к Bybit.\n\nОшибка: {error_msg}\n\n"
                "Возможные причины:\n"
                "1. Неверный API Key или Secret.\n"
                "2. Неверный тип аккаунта (нужен Unified Trading).\n"
                "3. IP адрес не добавлен в белый список Bybit.\n"
                "4. Проблемы с интернетом."
            )

    def save(self):
        tb = float(self.trading_balance.get() or "0")
        if not self.app.balance_service.validate_trading_balance(tb):
            return
            
        # First save settings
        self.app.settings.set("api_url", self.api_url.get().strip())
        self.app.settings.set("bybit_api_key", self.bybit_key.get().strip(), secure=True)
        self.app.settings.set("bybit_api_secret", self.bybit_secret.get().strip(), secure=True)
        self.app.settings.set("trading_balance", tb)
        self.app.settings.save()
        
        # Configure app which triggers connection test
        self.app.configure_bybit()
        
        # Check result
        if not self.app.connected_bybit:
             from tkinter import messagebox
             if not messagebox.askyesno("Ошибка подключения", "Не удалось подключиться к Bybit с указанными ключами. Сохранить настройки и закрыть?"):
                 return
        
        self.top.destroy()
        SettingsWindow.instance = None

    def logout(self):
        from tkinter import messagebox
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти из аккаунта?"):
            return
        try:
            self.app.auth.logout()
            self.app.settings.delete("token")
            self.app.settings.save()
            for w in list(self.top.master.winfo_children()):
                w.destroy()
            from ui.windows.login_window import LoginWindow
            LoginWindow(self.top.master, self.app)
        except Exception:
            pass
        self.top.destroy()
        SettingsWindow.instance = None
