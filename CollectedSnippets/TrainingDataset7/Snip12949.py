def pop(self, key, default=None):
        return self._store.pop(key.lower(), default)