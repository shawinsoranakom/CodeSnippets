def init_continuous_batching(
        self,
        generation_config: GenerationConfig | None = None,
        continuous_batching_config: ContinuousBatchingConfig | None = None,
        **deprecated_kwargs,
    ) -> ContinuousBatchingManager:
        """Initialize a manager for continuous batching inference.

        Args:
            generation_config: An optional generation configuration, which may contain a CompileConfig object
            continuous_batching_config: An optional continuous batching configuration
            **deprecated_kwargs: Deprecated arguments that are now passed in the continuous_batching_config. Those are:
                max_queue_size, q_padding_interval_size, kv_padding_interval_size, allow_block_sharing,
                use_async_batching, max_cached_graphs
        Returns:
            `ContinuousBatchingManager`: The manager instance to add requests and retrieve results.
        """
        # Mandatory attributes
        if not hasattr(self, "config") or not hasattr(self, "device") or not hasattr(self, "dtype"):
            raise AttributeError("Model must have 'config', 'device', and 'dtype' attributes.")

        # If a persistent manager is found we return it
        cached_manager = getattr(self, "_cached_continuous_batching_manager", None)
        if isinstance(cached_manager, ContinuousBatchingManager):
            logger.info(
                "Cached continuous batching manager found: it will be re-used instead of creating a new one. If you"
                " want to create a new manager, you should call `destroy_cached_continuous_batching_manager` first."
            )
            return cached_manager

        # Retrieve generation config
        gen_config = generation_config if generation_config is not None else self.generation_config
        if gen_config is None:
            raise ValueError("A GenerationConfig must be provided or set in the model.")
        # Warn about EOS
        if gen_config.eos_token_id is None:
            logger.warning("`eos_token_id` not set in GenerationConfig. Setting to -1 (disabled).")
            gen_config.eos_token_id = -1

        # Retrieve continuous batching config, or create it if none is provided
        if continuous_batching_config is None:
            if isinstance(getattr(gen_config, "continuous_batching_config", None), ContinuousBatchingConfig):
                continuous_batching_config = gen_config.continuous_batching_config
            else:
                continuous_batching_config = ContinuousBatchingConfig()
        continuous_batching_config.account_for_cb_deprecated_arguments(**deprecated_kwargs)

        # Create and return the manager
        return ContinuousBatchingManager(
            model=self, generation_config=gen_config, continuous_batching_config=continuous_batching_config
        )