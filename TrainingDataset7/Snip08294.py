def get(self, key, default=None, version=None):
        key = self.make_and_validate_key(key, version=version)
        return self._cache.get(key, default)