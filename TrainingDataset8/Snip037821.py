def write_result(self, key: str, value: Any, messages: List[MsgData]) -> None:
        """Write a value and associated messages to the cache.
        The value must be pickleable.
        """
        ctx = get_script_run_ctx()
        if ctx is None:
            return

        main_id = st._main.id
        sidebar_id = st.sidebar.id

        if self.allow_widgets:
            widgets = {
                msg.widget_metadata.widget_id
                for msg in messages
                if isinstance(msg, ElementMsgData) and msg.widget_metadata is not None
            }
        else:
            widgets = set()

        multi_cache_results: Optional[MultiCacheResults] = None

        # Try to find in mem cache, falling back to disk, then falling back
        # to a new result instance
        try:
            multi_cache_results = self._read_multi_results_from_mem_cache(key)
        except (CacheKeyNotFoundError, pickle.UnpicklingError):
            if self.persist == "disk":
                try:
                    multi_cache_results = self._read_multi_results_from_disk_cache(key)
                except CacheKeyNotFoundError:
                    pass

        if multi_cache_results is None:
            multi_cache_results = MultiCacheResults(widget_ids=widgets, results={})
        multi_cache_results.widget_ids.update(widgets)
        widget_key = multi_cache_results.get_current_widget_key(ctx, CacheType.MEMO)

        result = CachedResult(value, messages, main_id, sidebar_id)
        multi_cache_results.results[widget_key] = result

        try:
            pickled_entry = pickle.dumps(multi_cache_results)
        except pickle.PicklingError as exc:
            raise CacheError(f"Failed to pickle {key}") from exc

        self._write_to_mem_cache(key, pickled_entry)
        if self.persist == "disk":
            self._write_to_disk_cache(key, pickled_entry)