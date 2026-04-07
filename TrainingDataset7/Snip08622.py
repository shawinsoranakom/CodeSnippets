def readline(self, size=-1, /):
        _pos = self._pos
        limit = self.limit
        if _pos >= limit:
            return b""
        if size == -1 or size is None:
            size = limit - _pos
        else:
            size = min(size, limit - _pos)
        line = self._readline(size)
        self._pos += len(line)
        return line