def write_result(self, key: str, value: Any, messages: List[MsgData]) -> None:
        """Write a value and associated messages to the cache."""
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

        with self._mem_cache_lock:
            try:
                multi_results = self._mem_cache[key]
            except KeyError:
                multi_results = MultiCacheResults(widget_ids=widgets, results={})

            multi_results.widget_ids.update(widgets)
            widget_key = multi_results.get_current_widget_key(ctx, CacheType.SINGLETON)

            result = CachedResult(value, messages, main_id, sidebar_id)
            multi_results.results[widget_key] = result
            self._mem_cache[key] = multi_results