def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        if not self._cache.set(key, value, self.get_backend_timeout(timeout)):
            # Make sure the key doesn't keep its old value in case of failure
            # to set (memcached's 1MB limit).
            self._cache.delete(key)