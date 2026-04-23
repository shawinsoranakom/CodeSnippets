def account_for_cb_deprecated_arguments(
        self,
        max_queue_size: int = 0,
        q_padding_interval_size: int = 0,
        kv_padding_interval_size: int = 0,
        allow_block_sharing: bool = True,
        use_async_batching: bool | None = None,
        max_cached_graphs: int = 0,
    ) -> None:
        """Some arguments given to `generate_batch`, `init_continuous_batching` or `continuous_batching_context_manager`
        are now deprecated and are expected inside the continuous batching config. This method checks if any were
        passed and accounts for them in the continuous batching config. It raises a deprecation warning if any were
        passed.
        """
        kwargs_to_warn = []
        if max_queue_size > 0:
            kwargs_to_warn.append("max_queue_size")
            self.max_queue_size = max_queue_size
        if q_padding_interval_size > 0:
            kwargs_to_warn.append("q_padding_interval_size")
            self.q_padding_interval_size = q_padding_interval_size
        if kv_padding_interval_size > 0:
            kwargs_to_warn.append("kv_padding_interval_size")
            self.kv_padding_interval_size = kv_padding_interval_size
        if not allow_block_sharing:  # config default is True, so False means the user explicitly set it to False
            kwargs_to_warn.append("allow_block_sharing")
            self.allow_block_sharing = allow_block_sharing
        if use_async_batching is not None:
            kwargs_to_warn.append("use_async_batching")
            self.use_async_batching = use_async_batching
        if max_cached_graphs > 0:
            kwargs_to_warn.append("max_cached_graphs")
            self.max_cached_graphs = max_cached_graphs
        if kwargs_to_warn:
            logger.warning(
                "The following arguments were provided to a continuous batching entry point instead of being passed "
                "through the continuous_batching_config: " + ", ".join(kwargs_to_warn)
            )