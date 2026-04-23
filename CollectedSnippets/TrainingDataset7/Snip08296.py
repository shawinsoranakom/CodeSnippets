def touch(self, key, timeout=DEFAULT_TIMEOUT, version=None):
        key = self.make_and_validate_key(key, version=version)
        return bool(self._cache.touch(key, self.get_backend_timeout(timeout)))