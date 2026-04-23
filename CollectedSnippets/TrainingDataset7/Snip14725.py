def __getitem__(self, key):
        for cat in self._catalogs:
            try:
                return cat[key]
            except KeyError:
                pass
        raise KeyError(key)