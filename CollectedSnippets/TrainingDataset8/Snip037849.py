def clear(self) -> None:
        with self._mem_cache_lock:
            self._mem_cache.clear()