def iterator(self):
        yield from RawModelIterable(self)