def clear(self):
        with self._lock:
            self._cache.clear()
            self._expire_info.clear()