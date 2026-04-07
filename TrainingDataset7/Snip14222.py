def __delattr__(self, name):
        return delattr(self._connections[self._alias], name)