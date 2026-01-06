import threading
import time


class Scheduler:
    def __init__(self, logger):
        self.logger = logger
        self.tasks = {}
        self._running = False
        self._thread = None

    def add_task(self, name, interval, callback):
        self.tasks[name] = {"interval": interval, "callback": callback, "next": time.time() + interval}

    def remove_task(self, name):
        if name in self.tasks:
            del self.tasks[name]

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            now = time.time()
            for name, t in list(self.tasks.items()):
                if now >= t["next"]:
                    try:
                        t["callback"]()
                    except Exception as e:
                        self.logger.error("Scheduler task error", {"task": name, "error": str(e)})
                    t["next"] = now + t["interval"]
            time.sleep(0.1)
