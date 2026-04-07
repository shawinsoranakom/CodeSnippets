def get(self, key, default=None):
        missing = object()
        for cat in self._catalogs:
            result = cat.get(key, missing)
            if result is not missing:
                return result
        return default