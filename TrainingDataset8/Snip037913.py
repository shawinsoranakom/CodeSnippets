def get_stats(self) -> List[CacheStat]:
        with self._lock:
            # Shallow-clone our caches. We don't want to hold the global
            # lock during stats-gathering.
            function_caches = self._function_caches.copy()

        stats = [
            CacheStat("st_cache", cache.display_name, asizeof(c))
            for cache in function_caches.values()
            for c in cache.cache
        ]
        return stats