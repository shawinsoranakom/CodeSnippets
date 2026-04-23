def __getattr__(self, item):
        return getattr(self._connections[self._alias], item)