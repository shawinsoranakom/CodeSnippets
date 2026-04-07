def chunk_bytes(cls, data):
        """
        Chunks some data up so it can be sent in reasonable size messages.
        Yields (chunk, last_chunk) tuples.
        """
        position = 0
        if not data:
            yield data, True
            return
        while position < len(data):
            yield (
                data[position : position + cls.chunk_size],
                (position + cls.chunk_size) >= len(data),
            )
            position += cls.chunk_size