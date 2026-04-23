def __delitem__(self, key):
        del self._session[key]
        self.modified = True