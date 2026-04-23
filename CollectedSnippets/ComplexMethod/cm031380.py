def read(self, amt=None):
        """Read and return the response body, or up to the next amt bytes."""
        if self.fp is None:
            return b""

        if self._method == "HEAD":
            self._close_conn()
            return b""

        if self.chunked:
            return self._read_chunked(amt)

        if amt is not None and amt >= 0:
            if self.length is not None and amt > self.length:
                # clip the read to the "end of response"
                amt = self.length
            s = self.fp.read(amt)
            if not s and amt:
                # Ideally, we would raise IncompleteRead if the content-length
                # wasn't satisfied, but it might break compatibility.
                self._close_conn()
            elif self.length is not None:
                self.length -= len(s)
                if not self.length:
                    self._close_conn()
            return s
        else:
            # Amount is not given (unbounded read) so we must check self.length
            if self.length is None:
                s = self.fp.read()
            else:
                try:
                    s = self._safe_read(self.length)
                except IncompleteRead:
                    self._close_conn()
                    raise
                self.length = 0
            self._close_conn()        # we read everything
            return s