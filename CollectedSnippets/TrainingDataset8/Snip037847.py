def read_result(self, key: str) -> CachedResult:
        """Read a value and associated messages from the cache.
        Raise `CacheKeyNotFoundError` if the value doesn't exist.
        """
        with self._mem_cache_lock:
            if key in self._mem_cache:
                multi_results = self._mem_cache[key]

                ctx = get_script_run_ctx()
                if not ctx:
                    raise CacheKeyNotFoundError()

                widget_key = multi_results.get_current_widget_key(
                    ctx, CacheType.SINGLETON
                )
                if widget_key in multi_results.results:
                    return multi_results.results[widget_key]
                else:
                    raise CacheKeyNotFoundError()
            else:
                raise CacheKeyNotFoundError()