class EventBus:
    def __init__(self):
        self._subs = {}

    def subscribe(self, event_name, callback):
        self._subs.setdefault(event_name, set()).add(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self._subs and callback in self._subs[event_name]:
            self._subs[event_name].remove(callback)

    def emit(self, event_name, data):
        for cb in list(self._subs.get(event_name, [])):
            try:
                cb(data)
            except Exception:
                pass
