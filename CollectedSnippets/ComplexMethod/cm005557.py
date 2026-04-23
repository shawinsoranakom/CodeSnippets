def __init__(
        self,
        config: PreTrainedConfig,
        continuous_batching_config: ContinuousBatchingConfig,
        device: torch.device | str,
        dtype: torch.dtype = torch.float16,
        tp_size: int | None = None,
    ) -> None:
        """Initialize a paged attention cache for efficient memory usage. Also turns in prefix sharing if the model has
        only full attention layers.

        Args:
            config: Model configuration
            continuous_batching_config: Continuous batching configuration containing cache parameters
            device: Device for the cache tensors
            dtype: Data type of the cache
            tp_size: Tensor parallelism size
        """
        self.config = config
        self.dtype = dtype
        self.device = device

        # Extract model dimensions
        kv_heads = getattr(config, "num_key_value_heads", None)
        self.num_key_value_heads: int = kv_heads if kv_heads is not None else config.num_attention_heads
        head_dim = getattr(config, "head_dim", None)
        self.head_dim: int = head_dim if head_dim is not None else config.hidden_size // config.num_attention_heads

        # Extract cache dimensions. Default used to be 32, now it's 256 to be compatible with flash_with_kvcache.
        self.block_size = continuous_batching_config.block_size
        if self.block_size <= 0:
            raise ValueError(f"Block size must be positive, but got {self.block_size}")

        # Group layers depending on the attention mix
        layer_groups, group_types = group_layers_by_attn_type(config)
        group_size = len(layer_groups[0])
        self.num_groups = len(layer_groups)

        self.sliding_windows = {}
        self.layer_index_to_group_indices = {}
        for i, group in enumerate(layer_groups):
            sliding_window = config.sliding_window if group_types[i] == "sliding_attention" else 1
            for j, layer in enumerate(group):
                self.layer_index_to_group_indices[layer] = (i, j)
                self.sliding_windows[layer] = sliding_window

        # Handle TP (or dont)
        if tp_size is not None and tp_size > 1:
            if self.num_key_value_heads % tp_size != 0:
                raise ValueError(
                    f"Number of key value heads {self.num_key_value_heads} must be divisible by tensor parallel size {tp_size}."
                )
            # If the model is using tensor parallelism, we need to adjust the number of heads accordingly.
            # self.num_key_value_heads //= tp_size # TODO: why is this commented out?

        # Infer number of blocks and max batch tokens
        page_size = self.head_dim * self.num_key_value_heads

        if is_flash_attention_requested(self.config):
            num_attention_masks = 0  # only used to compute the default memory footprint args
        elif "sliding_attention" in group_types:
            # TODO: when we generalize to allow for block-attn, we can use `num_attention_masks=sum(set(group_types))`
            num_attention_masks = 2
        else:
            num_attention_masks = 1

        memory_handler = PagedAttentionMemoryHandler(
            block_size=self.block_size,
            page_size=page_size,
            num_groups=self.num_groups,
            group_size=group_size,
            peak_activation_per_token=(config.hidden_size + config.vocab_size),
            num_attention_masks=num_attention_masks,
            continuous_batching_config=continuous_batching_config,
        )
        num_blocks, max_batch_tokens = memory_handler.infer_num_blocks_and_max_batch_tokens(
            num_blocks=continuous_batching_config.num_blocks,
            max_batch_tokens=continuous_batching_config.max_batch_tokens,
            max_memory_percent=continuous_batching_config.max_memory_percent,
            cache_dtype=self.dtype,
        )

        # Add the inferred attributes to the class
        self.num_blocks = num_blocks
        self.max_batch_tokens = max_batch_tokens
        self.num_pages = self.num_blocks * self.block_size
        logger.info(
            f"PagedAttentionCache initialized with {self.num_blocks = }, {self.block_size = }, {page_size = }, "
            f"{self.max_batch_tokens = } {num_attention_masks = }"
        )

        # If max_blocks_per_request is not set, the default value is 16 max blocks. With default block size of 256, this
        # means a max sequence length of 4096 tokens for the fast decode path.
        max_blocks_per_request = continuous_batching_config.max_blocks_per_request
        if max_blocks_per_request is None:
            max_blocks_per_request = 0
            # logger.info( TODO: uncomment when we have good defaults
            #     f"max_blocks_per_request was not set, using {max_blocks_per_request}. This means max sequence "
            #     f"length for the decode fast path is {max_blocks_per_request * self.block_size}."
            # )
        self.max_blocks_per_request = max_blocks_per_request

        # Initialize the cache
        self.key_cache: list[torch.Tensor] = []
        self.value_cache: list[torch.Tensor] = []
        # We add two extra blocks to the cache as a padding zone that no BlockManager ever allocates from: one for the
        # sentinel index (marks the spot of a new token in the read indices) and one for the trash index (for padding,
        # block is never used so writes are silently discarded)
        self.cache_shape = ((num_blocks + 2) * self.block_size, self.num_key_value_heads, self.head_dim)
        self.sentinel_index = self.cache_shape[0] - 1
        self.trash_index = self.sentinel_index - 1
        for _ in range(group_size):
            new_layer_key_cache = torch.empty(self.cache_shape, dtype=self.dtype, device=self.device)
            new_layer_value_cache = torch.empty(self.cache_shape, dtype=self.dtype, device=self.device)
            torch._dynamo.mark_static_address(new_layer_key_cache)
            torch._dynamo.mark_static_address(new_layer_value_cache)
            self.key_cache.append(new_layer_key_cache)
            self.value_cache.append(new_layer_value_cache)
        logger.info(f"{self.cache_shape = } {self.key_cache[0].shape = } {self.key_cache[0].numel() = }")

        # Block management data structures
        self.allow_block_sharing = continuous_batching_config.allow_block_sharing
        self.group_cache_managers: list[CacheAllocator] = []
        self.num_full_attention_groups = 0
        self.num_sliding_attention_groups = 0
        self.max_sliding_window_blocks_per_request = 0

        for i, group_type in enumerate(group_types):
            if group_type == "full_attention":
                cm = FullAttentionCacheAllocator(i, self.block_size, allow_block_sharing=self.allow_block_sharing)
                self.num_full_attention_groups += 1
            elif group_type == "sliding_attention":
                cm = SlidingAttentionCacheAllocator(
                    i, self.block_size, config.sliding_window, self.sentinel_index, self.trash_index
                )
                self.num_sliding_attention_groups += 1
                self.max_sliding_window_blocks_per_request = cm._max_blocks_per_request
            else:
                raise ValueError(f"Invalid group type: {group_type}")
            self.group_cache_managers.append(cm)

        # We only use prefix sharing if the whole model has only full attention layers and block sharing is allowed
        self.use_prefix_sharing = self.allow_block_sharing and group_types == ["full_attention"]
        self._block_manager = BlockManager(num_blocks, self.block_size)
        self._total_prefix_length: int = 0  # a counter to measure the impact of prefix sharing, also used in tests

        # For block table support, we lazy init the name of the block table key
        self._block_table_key = None