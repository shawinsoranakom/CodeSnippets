def register_started(self, **kwargs):
        self.signals.append("started")
        self.signaled_environ = kwargs.get("environ")