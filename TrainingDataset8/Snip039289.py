def as_cached_result(value: Any, cache_type: CacheType) -> MultiCacheResults:
    """Creates cached results for a function that returned `value`
    and did not execute any elements.
    """
    result = CachedResult(value, [], st._main.id, st.sidebar.id)
    widget_key = _make_widget_key([], cache_type)
    d = {widget_key: result}
    initial = MultiCacheResults(set(), d)
    return initial