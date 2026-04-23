def get_cache(
        self, key: str, display_name: str, allow_widgets: bool
    ) -> "SingletonCache":
        """Return the mem cache for the given key.

        If it doesn't exist, create a new one with the given params.
        """

        # Get the existing cache, if it exists, and validate that its params
        # haven't changed.
        with self._caches_lock:
            cache = self._function_caches.get(key)
            if cache is not None:
                return cache

            # Create a new cache object and put it in our dict
            _LOGGER.debug("Creating new SingletonCache (key=%s)", key)
            cache = SingletonCache(
                key=key, display_name=display_name, allow_widgets=allow_widgets
            )
            self._function_caches[key] = cache
            return cache