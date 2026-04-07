def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        self._cache.set(key, value, self.get_backend_timeout(timeout))