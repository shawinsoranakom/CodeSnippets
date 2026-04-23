def _initialize_stream(self):
        """Initialize underlying stream according to the content type."""
        self.file = io.BytesIO() if self._content_type == bytes else io.StringIO()