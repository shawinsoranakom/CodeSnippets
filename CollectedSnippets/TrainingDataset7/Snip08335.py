def delete(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)
        return self._cache.delete(key)