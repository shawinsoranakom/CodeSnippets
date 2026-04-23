def __setitem__(self, key, value):
        self._session[key] = value
        self.modified = True