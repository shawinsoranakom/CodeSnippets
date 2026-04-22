def _read_multi_results_from_mem_cache(self, key: str) -> MultiCacheResults:
        """Look up the results and ensure it has the right type.

        Raises a `CacheKeyNotFoundError` if the key has no entry, or if the
        entry is malformed.
        """
        pickled = self._read_from_mem_cache(key)
        maybe_results = pickle.loads(pickled)
        if isinstance(maybe_results, MultiCacheResults):
            return maybe_results
        else:
            with self._mem_cache_lock:
                del self._mem_cache[key]
            raise CacheKeyNotFoundError()