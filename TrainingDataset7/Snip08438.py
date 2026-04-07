def multiple_chunks(self, chunk_size=None):
        """
        Return ``True`` if you can expect multiple chunks.

        NB: If a particular file representation is in memory, subclasses should
        always return ``False`` -- there's no good reason to read from memory
        in chunks.
        """
        return self.size > (chunk_size or self.DEFAULT_CHUNK_SIZE)