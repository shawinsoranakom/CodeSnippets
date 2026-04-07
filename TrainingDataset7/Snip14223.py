def __contains__(self, key):
        return key in self._connections[self._alias]