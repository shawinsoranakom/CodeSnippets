def readline(self, limit=-1):
        if self.fp is None or self._method == "HEAD":
            return b""
        if self.chunked:
            # Fallback to IOBase readline which uses peek() and read()
            return super().readline(limit)
        if self.length is not None and (limit < 0 or limit > self.length):
            limit = self.length
        result = self.fp.readline(limit)
        if not result and limit:
            self._close_conn()
        elif self.length is not None:
            self.length -= len(result)
            if not self.length:
                self._close_conn()
        return result