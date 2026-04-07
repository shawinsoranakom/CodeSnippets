def __iter__(self):
        return (original_key for original_key, value in self._store.values())