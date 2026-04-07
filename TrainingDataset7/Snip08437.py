def chunks(self, chunk_size=None):
        """
        Read the file and yield chunks of ``chunk_size`` bytes (defaults to
        ``File.DEFAULT_CHUNK_SIZE``).
        """
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        try:
            self.seek(0)
        except (AttributeError, UnsupportedOperation):
            pass

        while True:
            data = self.read(chunk_size)
            if not data:
                break
            yield data