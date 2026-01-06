class WebSocketClient:
    def __init__(self, logger):
        self.logger = logger
        self._running = False

    def start(self):
        self._running = True

    def stop(self):
        self._running = False
