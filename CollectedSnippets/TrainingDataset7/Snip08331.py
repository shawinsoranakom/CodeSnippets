def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        return self._cache.add(key, value, self.get_backend_timeout(timeout))