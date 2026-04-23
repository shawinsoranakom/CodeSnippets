def get_stats(self) -> List[CacheStat]:
        """Return a list containing all stats from each registered provider."""
        all_stats: List[CacheStat] = []
        for provider in self._cache_stats_providers:
            all_stats.extend(provider.get_stats())
        return all_stats