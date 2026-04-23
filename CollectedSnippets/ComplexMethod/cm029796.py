def seek(self, pos, whence=0):
        if self.closed:
            raise ValueError("seek on closed file")
        try:
            pos_index = pos.__index__
        except AttributeError:
            raise TypeError(f"{pos!r} is not an integer")
        else:
            pos = pos_index()
        if whence == 0:
            if pos < 0:
                raise ValueError("negative seek position %r" % (pos,))
            self._pos = pos
        elif whence == 1:
            with self._lock:
                self._pos = max(0, self._pos + pos)
        elif whence == 2:
            with self._lock:
                self._pos = max(0, len(self._buffer) + pos)
        else:
            raise ValueError("unsupported whence value")
        return self._pos