def clear(self) -> None:
        with self._mem_cache_lock:
            # We keep a lock for the entirety of the clear operation to avoid
            # disk cache race conditions.
            for key in self._mem_cache.keys():
                self._remove_from_disk_cache(key)

            self._mem_cache.clear()