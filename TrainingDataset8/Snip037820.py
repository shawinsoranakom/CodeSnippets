def read_result(self, key: str) -> CachedResult:
        """Read a value and messages from the cache. Raise `CacheKeyNotFoundError`
        if the value doesn't exist, and `CacheError` if the value exists but can't
        be unpickled.
        """
        try:
            pickled_entry = self._read_from_mem_cache(key)

        except CacheKeyNotFoundError as e:
            if self.persist == "disk":
                pickled_entry = self._read_from_disk_cache(key)
                self._write_to_mem_cache(key, pickled_entry)
            else:
                raise e

        try:
            entry = pickle.loads(pickled_entry)
            if not isinstance(entry, MultiCacheResults):
                # Loaded an old cache file format, remove it and let the caller
                # rerun the function.
                self._remove_from_disk_cache(key)
                raise CacheKeyNotFoundError()

            ctx = get_script_run_ctx()
            if not ctx:
                raise CacheKeyNotFoundError()

            widget_key = entry.get_current_widget_key(ctx, CacheType.MEMO)
            if widget_key in entry.results:
                return entry.results[widget_key]
            else:
                raise CacheKeyNotFoundError()
        except pickle.UnpicklingError as exc:
            raise CacheError(f"Failed to unpickle {key}") from exc