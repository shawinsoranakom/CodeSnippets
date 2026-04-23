def get_stats(self) -> List[CacheStat]:
        stats: List[CacheStat] = []
        with self._mem_cache_lock:
            for item_key, item_value in self._mem_cache.items():
                stats.append(
                    CacheStat(
                        category_name="st_memo",
                        cache_name=self.display_name,
                        byte_length=len(item_value),
                    )
                )
        return stats