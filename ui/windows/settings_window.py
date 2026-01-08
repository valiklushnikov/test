import tkinter as tk
from tkinter import ttk, messagebox
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
        self.top.geometry("500x500")
        self.top.resizable(False, False)
        SettingsWindow.instance = self

        # Флаг для предотвращения множественных операций
        self._is_testing = False
        self._is_saving = False

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

        # Кнопка тестирования с индикатором
        test_frame = ttk.Frame(frame)
        test_frame.grid(row=8, column=0, sticky="ew", pady=4)

        self.test_button = ttk.Button(test_frame, text="Проверить подключение", command=self.test_connection)
        self.test_button.pack(side="left", fill="x", expand=True)

        self.test_progress = ttk.Progressbar(test_frame, mode="indeterminate", length=50)

        # Статус подключения
        self.status_label = ttk.Label(frame, text="", foreground="gray")
        self.status_label.grid(row=9, column=0, sticky="w")

        ttk.Separator(frame).grid(row=10, column=0, sticky="ew", pady=8)

        ttk.Label(frame, text="Баланс кошелька:").grid(row=11, column=0, sticky="w")
        self.wallet_balance = tk.StringVar(value=f"{self.app.balance_service.wallet_balance:.2f}")
        ttk.Label(frame, textvariable=self.wallet_balance).grid(row=12, column=0, sticky="w")

        ttk.Label(frame, text="Торговый баланс:").grid(row=13, column=0, sticky="w")
        self.trading_balance = tk.StringVar(value=str(self.app.settings.get("trading_balance", "0")))
        ttk.Entry(frame, textvariable=self.trading_balance, width=20).grid(row=14, column=0, sticky="w")

        # Кнопка сохранения с индикатором
        save_frame = ttk.Frame(frame)
        save_frame.grid(row=15, column=0, sticky="ew", pady=8)

        self.save_button = ttk.Button(save_frame, text="Сохранить", command=self.save)
        self.save_button.pack(side="left", fill="x", expand=True)

        self.save_progress = ttk.Progressbar(save_frame, mode="indeterminate", length=50)

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
            self.top.update()

    def test_connection(self):
        """Асинхронная проверка подключения"""
        if self._is_testing:
            return

        key = self.bybit_key.get().strip()
        secret = self.bybit_secret.get().strip()

        if not is_valid_api_key(key) or not is_valid_api_key(secret):
            messagebox.showerror("Ошибка", "API ключи имеют неверный формат.")
            return

        # Блокируем кнопку и показываем прогресс
        self._is_testing = True
        self.test_button.config(state="disabled")
        self.test_progress.pack(side="left", padx=(5, 0))
        self.test_progress.start(10)
        self.status_label.config(text="Проверка подключения...", foreground="blue")

        # Запускаем в отдельном потоке
        threading.Thread(target=self._test_connection_async, args=(key, secret), daemon=True).start()

    def _test_connection_async(self, key, secret):
        """Фоновая проверка подключения"""
        try:
            # Сохраняем ключи временно
            self.app.settings.set("bybit_api_key", key, secure=True)
            self.app.settings.set("bybit_api_secret", secret, secure=True)

            # Переинициализируем Bybit API
            from api.bybit_api import BybitAPI
            test_api = BybitAPI(key, secret)
            test_api.connect()

            # Тестируем подключение
            ok = test_api.test_connection()

            if ok:
                # Получаем баланс
                balance = test_api.get_balance()

                # Обновляем UI в главном потоке
                self.top.after(0, lambda: self._on_test_success(balance))
            else:
                error_msg = test_api.last_error or "Неизвестная ошибка"
                self.top.after(0, lambda: self._on_test_failure(error_msg))

        except Exception as e:
            self.top.after(0, lambda: self._on_test_failure(str(e)))

    def _on_test_success(self, balance):
        """Обработка успешного подключения (в главном потоке)"""
        self._is_testing = False
        self.test_button.config(state="normal")
        self.test_progress.stop()
        self.test_progress.pack_forget()

        self.status_label.config(text="✓ Подключено успешно", foreground="green")
        self.wallet_balance.set(f"{balance:.2f}")

        # Обновляем app
        self.app.configure_bybit()

        messagebox.showinfo("Успех", "Подключение к Bybit установлено успешно!")

    def _on_test_failure(self, error_msg):
        """Обработка ошибки подключения (в главном потоке)"""
        self._is_testing = False
        self.test_button.config(state="normal")
        self.test_progress.stop()
        self.test_progress.pack_forget()

        self.status_label.config(text="✗ Ошибка подключения", foreground="red")

        messagebox.showerror("Ошибка подключения",
                             f"Не удалось подключиться к Bybit.\n\nОшибка: {error_msg}\n\n"
                             "Возможные причины:\n"
                             "1. Неверный API Key или Secret.\n"
                             "2. Неверный тип аккаунта (нужен Unified Trading).\n"
                             "3. IP адрес не добавлен в белый список Bybit.\n"
                             "4. Проблемы с интернетом."
                             )

    def save(self):
        """Асинхронное сохранение настроек"""
        if self._is_saving:
            return

        try:
            tb = float(self.trading_balance.get() or "0")
        except ValueError:
            messagebox.showerror("Ошибка", "Торговый баланс должен быть числом")
            return

        # Блокируем кнопку и показываем прогресс
        self._is_saving = True
        self.save_button.config(state="disabled")
        self.save_progress.pack(side="left", padx=(5, 0))
        self.save_progress.start(10)

        # Запускаем в отдельном потоке
        key = self.bybit_key.get().strip()
        secret = self.bybit_secret.get().strip()
        if not key and not secret:
            self.top.after(0, lambda: self._on_save_error("Не установлены API ключи"))
            return
        api_url = self.api_url.get().strip()

        threading.Thread(target=self._save_async, args=(api_url, key, secret, tb), daemon=True).start()

    def _save_async(self, api_url, key, secret, tb):
        """Фоновое сохранение настроек"""
        try:
            # Проверяем trading balance
            if not self.app.balance_service.validate_trading_balance(tb):
                self.top.after(0, lambda: self._on_save_error("Торговый баланс превышает баланс кошелька"))
                return

            # Сохраняем настройки
            self.app.settings.set("api_url", api_url)
            self.app.settings.set("bybit_api_key", key, secure=True)
            self.app.settings.set("bybit_api_secret", secret, secure=True)
            self.app.settings.set("trading_balance", tb)
            self.app.settings.save()


            # Настраиваем Bybit
            self.app.configure_bybit()

            # Проверяем результат
            if not self.app.connected_bybit and (key and secret):
                # Даем пользователю выбор
                self.top.after(0, self._confirm_save_with_error)
            else:
                self.top.after(0, self._on_save_success)

        except Exception as e:
            self.top.after(0, lambda: self._on_save_error(str(e)))

    def _confirm_save_with_error(self):
        """Подтверждение сохранения при ошибке подключения"""
        self._is_saving = False
        self.save_button.config(state="normal")
        self.save_progress.stop()
        self.save_progress.pack_forget()

        if messagebox.askyesno("Ошибка подключения",
                               "Не удалось подключиться к Bybit с указанными ключами.\n\n"
                               "Сохранить настройки и закрыть?"):
            self.top.destroy()
            SettingsWindow.instance = None
        else:
            self._is_saving = False

    def _on_save_success(self):
        """Успешное сохранение"""
        self._is_saving = False
        self.save_button.config(state="normal")
        self.save_progress.stop()
        self.save_progress.pack_forget()

        messagebox.showinfo("Успех", "Настройки сохранены успешно!")
        self.top.destroy()
        SettingsWindow.instance = None

    def _on_save_error(self, error_msg):
        """Ошибка при сохранении"""
        self._is_saving = False
        self.save_button.config(state="normal")
        self.save_progress.stop()
        self.save_progress.pack_forget()

        messagebox.showerror("Ошибка", f"Не удалось сохранить настройки:\n{error_msg}")

    def logout(self):
        if not messagebox.askyesno("Подтверждение", "Вы уверены, что хотите выйти из аккаунта?"):
            return
        try:
            self.app.auth.logout()
            self.app.settings.delete("token")
            self.app.settings.save()

            # Закрываем все окна и возвращаемся к логину
            for w in list(self.top.master.winfo_children()):
                w.destroy()

            from ui.windows.login_window import LoginWindow
            LoginWindow(self.top.master, self.app)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при выходе: {e}")

        self.top.destroy()
        SettingsWindow.instance = None