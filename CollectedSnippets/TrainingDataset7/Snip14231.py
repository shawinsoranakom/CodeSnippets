def __delitem__(self, key):
        delattr(self._connections, key)