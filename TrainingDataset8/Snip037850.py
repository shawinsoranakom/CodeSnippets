def get_stats(self) -> List[CacheStat]:
        # Shallow clone our cache. Computing item sizes is potentially
        # expensive, and we want to minimize the time we spend holding
        # the lock.
        with self._mem_cache_lock:
            mem_cache = self._mem_cache.copy()

        stats: List[CacheStat] = []
        for item_key, item_value in mem_cache.items():
            stats.append(
                CacheStat(
                    category_name="st_singleton",
                    cache_name=self.display_name,
                    byte_length=asizeof.asizeof(item_value),
                )
            )
        return stats