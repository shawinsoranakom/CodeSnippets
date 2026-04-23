def setdefault(self, key, value):
        if key in self._session:
            return self._session[key]
        else:
            self[key] = value
            return value