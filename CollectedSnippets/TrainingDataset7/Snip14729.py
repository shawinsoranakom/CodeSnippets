def keys(self):
        for cat in self._catalogs:
            yield from cat.keys()