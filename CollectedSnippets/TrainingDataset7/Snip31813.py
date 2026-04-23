def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This event is set right after the first time a request closes its
        # database connections.
        self._connections_closed = threading.Event()