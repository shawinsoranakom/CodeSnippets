def __setitem__(self, key, value):
        setattr(self._connections, key, value)