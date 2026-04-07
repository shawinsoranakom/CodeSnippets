def delete(self, key, version=None):
        key = self.make_and_validate_key(key, version=version)
        return bool(self._cache.delete(key))