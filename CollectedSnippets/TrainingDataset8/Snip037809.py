def get_cache(
        self,
        key: str,
        persist: Optional[str],
        max_entries: Optional[Union[int, float]],
        ttl: Optional[Union[int, float]],
        display_name: str,
        allow_widgets: bool,
    ) -> "MemoCache":
        """Return the mem cache for the given key.

        If it doesn't exist, create a new one with the given params.
        """
        if max_entries is None:
            max_entries = math.inf
        if ttl is None:
            ttl = math.inf

        # Get the existing cache, if it exists, and validate that its params
        # haven't changed.
        with self._caches_lock:
            cache = self._function_caches.get(key)
            if (
                cache is not None
                and cache.ttl == ttl
                and cache.max_entries == max_entries
                and cache.persist == persist
            ):
                return cache

            # Create a new cache object and put it in our dict
            _LOGGER.debug(
                "Creating new MemoCache (key=%s, persist=%s, max_entries=%s, ttl=%s)",
                key,
                persist,
                max_entries,
                ttl,
            )
            cache = MemoCache(
                key=key,
                persist=persist,
                max_entries=max_entries,
                ttl=ttl,
                display_name=display_name,
                allow_widgets=allow_widgets,
            )
            self._function_caches[key] = cache
            return cache