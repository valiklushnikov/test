import tkinter as tk
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
logger.set_sink(lambda level, message, data, ts: events.emit("on_ui_log", {"level": level, "message": f"{message}", "data": data, "ts": ts}))


def run():
    root = tk.Tk()
    root.title("ManekiTerminal v0.0.1")
    img = Image.open(icons_dir / "favicon-b.png")
    icon = ImageTk.PhotoImage(img)
    root.iconphoto(True, icon)
    auth.load_session()
    if auth.is_authenticated():
        logger.info("Авто-авторизация успешна")
        MainWindow(root, app)
    else:
        logger.info("Ожидание авторизации")
        LoginWindow(root, app)
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
