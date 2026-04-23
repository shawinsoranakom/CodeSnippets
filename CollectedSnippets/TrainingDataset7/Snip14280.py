def __getitem__(self, key):
        return self._store[key.lower()][1]