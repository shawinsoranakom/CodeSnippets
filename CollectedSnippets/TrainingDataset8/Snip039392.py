def as_cached_result(value: Any) -> MultiCacheResults:
    return _as_cached_result(value, CacheType.MEMO)