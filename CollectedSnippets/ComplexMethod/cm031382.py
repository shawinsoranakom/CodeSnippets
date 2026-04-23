def _read_chunked(self, amt=None):
        assert self.chunked != _UNKNOWN
        if amt is not None and amt < 0:
            amt = None
        value = []
        try:
            while (chunk_left := self._get_chunk_left()) is not None:
                if amt is not None and amt <= chunk_left:
                    value.append(self._safe_read(amt))
                    self.chunk_left = chunk_left - amt
                    break

                value.append(self._safe_read(chunk_left))
                if amt is not None:
                    amt -= chunk_left
                self.chunk_left = 0
            return b''.join(value)
        except IncompleteRead as exc:
            raise IncompleteRead(b''.join(value)) from exc