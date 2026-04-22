def clear_cache() -> bool:
    """Clear the memoization cache.

    Returns
    -------
    boolean
        True if the disk cache was cleared. False otherwise (e.g. cache file
        doesn't exist on disk).
    """
    _clear_mem_cache()
    return _clear_disk_cache()