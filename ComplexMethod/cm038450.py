def __post_init__(self):
        self.local_physical_heads = max(1, self.total_num_kv_heads // self.tp_size)

        self._engines: dict[EngineId, EngineTransferInfo] = {}
        self._fa_source_sets: dict[EngineId, frozenset[int]] = {}
        self._fa_source_indices: dict[EngineId, dict[int, int]] = {}

        # Figure out whether the first dimension of the cache is K/V
        # or num_blocks.
        attn_backend = self.attn_backends[0]
        if not self.is_mamba:
            _MOCK_BLOCK_SIZE = 16
            kv_cache_shape: tuple[int, ...] = attn_backend.get_kv_cache_shape(
                num_blocks=1,
                block_size=_MOCK_BLOCK_SIZE,
                num_kv_heads=1,
                head_size=1,
            )
            logger.debug("Test kv_cache_shape: %s", kv_cache_shape)
        # Non-MLA backends caches have 5 dims [2, num_blocks, H,N,D],
        # we just mock num_blocks to 1 for the dimension check below.
        # Hybrid SSM models assume a single blocks_first layout
        self._is_kv_layout_blocks_first = self.is_mamba or (
            len(kv_cache_shape) == 5 and kv_cache_shape[0] == 1
        )

        self._cross_layers_blocks = False
        if self.tensor_shape is not None:
            self._cross_layers_blocks = (
                len(self.tensor_shape) == len(kv_cache_shape) + 1
            )

        if self._cross_layers_blocks:
            logger.debug("Using cross-layer KV cache")
            _MOCK_NUM_LAYERS = 80
            kv_cache_shape = (_MOCK_NUM_LAYERS,) + kv_cache_shape
            try:
                kv_cache_stride_order = attn_backend.get_kv_cache_stride_order(
                    include_num_layers_dimension=self._cross_layers_blocks
                )
            except (AttributeError, NotImplementedError):
                assert self.tensor_shape is not None
                kv_cache_stride_order = tuple(range(len(self.tensor_shape)))
            kv_cache_shape = tuple(kv_cache_shape[i] for i in kv_cache_stride_order)