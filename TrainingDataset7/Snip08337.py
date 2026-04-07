def has_key(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)
        return self._cache.has_key(key)