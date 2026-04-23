def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_handler = DummyHandler()
        self._used_sendfile = False