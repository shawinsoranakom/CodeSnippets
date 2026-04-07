def __init__(self, settings=None):
        self._settings = settings
        self._connections = Local(self.thread_critical)