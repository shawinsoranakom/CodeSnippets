def __repr__(self):
        start = self.start - 1
        stop = None if self.length is None else start + self.length
        subscript = slice(start, stop)
        return f"{self.__class__.__qualname__}({self.obj!r}, {subscript!r})"