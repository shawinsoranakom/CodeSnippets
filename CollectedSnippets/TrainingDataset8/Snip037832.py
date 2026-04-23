def get_singleton_stats_provider() -> CacheStatsProvider:
    """Return the StatsProvider for all singleton functions."""
    return _singleton_caches