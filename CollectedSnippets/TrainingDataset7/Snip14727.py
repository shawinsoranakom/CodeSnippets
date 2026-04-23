def __contains__(self, key):
        return any(key in cat for cat in self._catalogs)