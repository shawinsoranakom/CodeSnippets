def incr(self, key, delta=1, version=None):
        key = self.make_and_validate_key(key, version=version)
        return self._cache.incr(key, delta)