def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_handler = DummyHandler()
        self.headers_written = False
        self.write_chunk_counter = 0