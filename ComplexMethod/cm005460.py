def __init__(
        self,
        model: PreTrainedModel,
        batch_size: int | None = None,
        max_cache_len: int | None = None,
        device: torch.device | None = None,
    ) -> None:
        """
        Initializes the wrapper module with the pretrained model.

        Args:
            model (`PreTrainedModel`): The pretrained model to wrap. The model must have caching
                enabled and use a 'static' caching implementation.
            batch_size (`Optional[int]`): The batch size of the model. If not provided, we check if a value can be found
                in `generation_config.cache_config` and otherwise we raise a ValueError.
            max_cache_len (`Optional[int]`): The maximum cache length for generation. Same mechanism as `batch_size` if
                not provided.
            device (`Optional[torch.device]`): The device to use. If not provided, we check if a value can be found
                in `generation_config.cache_config` and otherwise we use `model.device` (no error is raised).

        Raises:
            AssertionError: If the pretrained model does not have caching enabled or if it does
            not use a 'static' caching implementation in `model.generation_config`.
            ValueError: If `batch_size` or `max_cache_len` is not provided, either as an argument or in `cache_config`.
        """
        super().__init__()

        config = model.config.get_text_config()
        generation_config = model.generation_config

        # Sanity checks
        if generation_config is None:
            raise AssertionError(
                "The model must have a generation config to be exported with static caching. "
                "Please set `generation_config` in `model`."
            )
        if not generation_config.use_cache:
            raise AssertionError(
                "The model must have caching enabled to be exported with static caching. "
                "Please set `generation_config.use_cache=True`."
            )
        if generation_config.cache_implementation != "static":
            raise AssertionError(
                "The model must use a 'static' caching implementation to be exported with static caching. "
                "Please set `generation_config.cache_implementation='static'`."
            )

        cache_config = {} if generation_config.cache_config is None else generation_config.cache_config

        # Ensure batch_size and max_cache_len are set
        if batch_size is None:
            batch_size = cache_config.get("batch_size", None)
            if batch_size is None:
                raise ValueError("batch_size must be provided, either as an argument or in cache_config.")
        if max_cache_len is None:
            max_cache_len = cache_config.get("max_cache_len", None)
            if max_cache_len is None:
                raise ValueError("max_cache_len must be provided, either as an argument or in cache_config.")
        # Infer device if not provided
        if device is None:
            device = cache_config.get("device", model.device)

        # Initialize the static cache
        self.model = model
        self.static_cache = StaticCache(max_cache_len=max_cache_len, config=config)
        # Since StaticSlidingWindow have dynamic control flow that cannot be avoided, we have to replace them here by
        # simple StaticLayer... It means that any generation beyond the window is unfortunately unsupported
        for i, layer in enumerate(self.static_cache.layers):
            if isinstance(layer, StaticSlidingWindowLayer):
                self.static_cache.layers[i] = StaticLayer(max_cache_len)
        num_heads, head_dim = get_head_shapes(config)
        dtype = self.model.dtype
        # We need this call to initialize all the layers (otherwise it's done lazily, which is not exportable)
        self.static_cache.early_initialization(batch_size, num_heads, head_dim, dtype, device)

        # Register cache buffers to make them exportable
        for i, layer in enumerate(self.static_cache.layers):
            self.register_buffer(f"key_cache_{i}", layer.keys, persistent=False)
            self.register_buffer(f"value_cache_{i}", layer.values, persistent=False)
            self.register_buffer(f"cumulative_length_{i}", layer.cumulative_length, persistent=False)