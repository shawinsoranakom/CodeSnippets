def __setattr__(self, name, value):
        return setattr(self._connections[self._alias], name, value)