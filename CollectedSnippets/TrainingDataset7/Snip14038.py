def clear_url_caches():
    get_callable.cache_clear()
    _get_cached_resolver.cache_clear()
    get_ns_resolver.cache_clear()