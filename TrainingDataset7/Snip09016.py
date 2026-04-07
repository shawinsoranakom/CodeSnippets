def __next__(self):
        if self._iterator is None:
            self._iterator = iter(self)
        return next(self._iterator)