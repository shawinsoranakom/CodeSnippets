def __call__(self, signal, **kwargs):
        self.calls.append({"thread": threading.current_thread(), "kwargs": kwargs})