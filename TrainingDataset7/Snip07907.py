def get(self, key, default=None):
        return self._session.get(key, default)