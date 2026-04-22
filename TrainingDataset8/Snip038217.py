def invalidate_pages_cache():
    global _cached_pages

    LOGGER.debug("Pages directory changed")
    with _pages_cache_lock:
        _cached_pages = None

    _on_pages_changed.send()