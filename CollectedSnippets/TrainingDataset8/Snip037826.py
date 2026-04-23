def _read_multi_results_from_disk_cache(self, key: str) -> MultiCacheResults:
        """Look up the results from disk and ensure it has the right type.

        Raises a `CacheKeyNotFoundError` if the key has no entry, or if the
        entry is the wrong type, which usually means it was written by another
        version of streamlit.
        """
        pickled = self._read_from_disk_cache(key)
        maybe_results = pickle.loads(pickled)
        if isinstance(maybe_results, MultiCacheResults):
            return maybe_results
        else:
            self._remove_from_disk_cache(key)
            raise CacheKeyNotFoundError("Key not found in disk cache")