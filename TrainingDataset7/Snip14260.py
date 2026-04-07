def __getstate__(self):
        return {**self.__dict__, "_data": {k: self._getlist(k) for k in self}}