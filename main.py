import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from pathlib import Path
from core.app import App
from core.auth import AuthManager
from core.events import EventBus
from core.scheduler import Scheduler
from ui.windows.login_window import LoginWindow
from ui.windows.main_window import MainWindow
from utils.logger import Logger
from storage.settings import Settings

from database.db import Database
from database.migrations import run_migrations

base_dir = Path(__file__).resolve().parent

logs_dir = base_dir / "logs"
data_dir = base_dir / "data"
icons_dir = base_dir / "icons"

logs_dir.mkdir(parents=True, exist_ok=True)
data_dir.mkdir(parents=True, exist_ok=True)
icons_dir.mkdir(parents=True, exist_ok=True)

# Инициализация БД
db = Database(data_dir / "terminal.db")
run_migrations(db)

logger = Logger(logs_dir, retention_days=30)
settings = Settings(data_dir)
auth = AuthManager(settings, logger)
events = EventBus()
scheduler = Scheduler(logger)
app = App(auth, events, scheduler, settings, logger, db)
logger.set_sink(lambda level, message, data, ts: events.emit("on_ui_log",
                                                             {"level": level, "message": f"{message}", "data": data,
                                                              "ts": ts}))


def show_splash(root):
    """Показать splash screen на время инициализации"""
    splash = tk.Toplevel(root)
    splash.overrideredirect(True)  # Убираем рамку окна

    # Размер splash
    w, h = 300, 150
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    # Содержимое splash - используем ttk.Frame с padding
    frame = ttk.Frame(splash, padding=20)
    frame.pack(fill="both", expand=True)

    # Используем ttk.Label
    ttk.Label(frame, text="ManekiTerminal v0.0.1", font=("Segoe UI", 16, "bold")).pack(pady=10)
    ttk.Label(frame, text="Загрузка...", font=("Segoe UI", 10)).pack(pady=5)

    # Используем ttk.Progressbar
    progress = ttk.Progressbar(frame, mode="indeterminate", length=200)
    progress.pack(pady=10)
    progress.start(10)

    return splash


def run():
    root = tk.Tk()
    root.title("ManekiTerminal v0.0.1")

    # Устанавливаем иконку если файл существует
    icon_path = icons_dir / "favicon-b.png"
    if icon_path.exists():
        try:
            img = Image.open(icon_path)
            icon = ImageTk.PhotoImage(img)
            root.iconphoto(True, icon)
        except Exception as e:
            logger.warning("Failed to load icon", {"error": str(e)})

    root.withdraw()  # Скрываем главное окно

    # Показываем splash
    splash = show_splash(root)
    root.update()

    # Загружаем сессию (это быстрая операция)
    auth.load_session()

    # Определяем какое окно показывать
    if auth.is_authenticated():
        logger.info("Авто-авторизация успешна")
        # Для авторизованного пользователя сразу показываем главное окно
        # Инициализация данных будет происходить асинхронно в MainWindow
        MainWindow(root, app)
    else:
        logger.info("Ожидание авторизации")
        LoginWindow(root, app)

    # Обновляем геометрию перед показом
    root.update_idletasks()

    # Центрируем окно
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    root.geometry(f"+{x}+{y}")

    # Закрываем splash и показываем главное окно
    splash.destroy()
    root.deiconify()

    root.mainloop()


if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logger.error("Unhandled exception", {"error": str(e)})
    finally:
        # Очистка ресурсов
        try:
            app.stop()
        except:
            pass