def readinto(self, b):
        """Read up to len(b) bytes into bytearray b and return the number
        of bytes read.
        """

        if self.fp is None:
            return 0

        if self._method == "HEAD":
            self._close_conn()
            return 0

        if self.chunked:
            return self._readinto_chunked(b)

        if self.length is not None:
            if len(b) > self.length:
                # clip the read to the "end of response"
                b = memoryview(b)[0:self.length]

        # we do not use _safe_read() here because this may be a .will_close
        # connection, and the user is reading more bytes than will be provided
        # (for example, reading in 1k chunks)
        n = self.fp.readinto(b)
        if not n and b:
            # Ideally, we would raise IncompleteRead if the content-length
            # wasn't satisfied, but it might break compatibility.
            self._close_conn()
        elif self.length is not None:
            self.length -= n
            if not self.length:
                self._close_conn()
        return n