def __setitem__(self, key, value):
        key = self._convert_to_charset(key, "ascii")
        value = self._convert_to_charset(value, "latin-1", mime_encode=True)
        self._store[key.lower()] = (key, value)