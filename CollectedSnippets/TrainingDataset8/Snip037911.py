def get_cache(
        self,
        key: str,
        max_entries: Optional[float],
        ttl: Optional[float],
        display_name: str = "",
    ) -> MemCache:
        """Return the mem cache for the given key.

        If it doesn't exist, create a new one with the given params.
        """

        if max_entries is None:
            max_entries = math.inf
        if ttl is None:
            ttl = math.inf

        if not isinstance(max_entries, (int, float)):
            raise RuntimeError("max_entries must be an int")
        if not isinstance(ttl, (int, float)):
            raise RuntimeError("ttl must be a float")

        # Get the existing cache, if it exists, and validate that its params
        # haven't changed.
        with self._lock:
            mem_cache = self._function_caches.get(key)
            if (
                mem_cache is not None
                and mem_cache.cache.ttl == ttl
                and mem_cache.cache.maxsize == max_entries
            ):
                return mem_cache

            # Create a new cache object and put it in our dict
            _LOGGER.debug(
                "Creating new mem_cache (key=%s, max_entries=%s, ttl=%s)",
                key,
                max_entries,
                ttl,
            )
            ttl_cache = TTLCache(maxsize=max_entries, ttl=ttl, timer=_TTLCACHE_TIMER)
            mem_cache = MemCache(ttl_cache, display_name)
            self._function_caches[key] = mem_cache
            return mem_cache