def get_memo_stats_provider() -> CacheStatsProvider:
    """Return the StatsProvider for all memoized functions."""
    return _memo_caches