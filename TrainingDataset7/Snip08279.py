def _set(self, key, value, timeout=DEFAULT_TIMEOUT):
        if len(self._cache) >= self._max_entries:
            self._cull()
        self._cache[key] = value
        self._cache.move_to_end(key, last=False)
        self._expire_info[key] = self.get_backend_timeout(timeout)