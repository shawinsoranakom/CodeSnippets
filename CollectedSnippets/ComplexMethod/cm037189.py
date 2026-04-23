def __init__(
        self,
        kv_cache_spec: AttentionSpec,
        layer_names: list[str],
        vllm_config: VllmConfig,
        device: torch.device,
    ):
        super().__init__(kv_cache_spec, layer_names, vllm_config, device)

        self.model_config = vllm_config.model_config
        self.parallel_config = vllm_config.parallel_config
        self.cache_config = vllm_config.cache_config

        self.num_heads_q = self.model_config.get_num_attention_heads(
            self.parallel_config
        )
        self.num_heads_kv = self.model_config.get_num_kv_heads(self.parallel_config)
        self.headdim = self.model_config.get_head_size()
        self.block_size = kv_cache_spec.block_size
        # Sliding window size to be used with the AOT scheduler will be
        # populated on first build() call.
        self.aot_sliding_window: tuple[int, int] | None = None
        self.total_tokens: int = 0
        self._init_reorder_batch_threshold(1, supports_spec_as_decode=True)

        sliding_window_configs: set[tuple[int, int] | None] = set()
        layers = get_layers_from_vllm_config(self.vllm_config, Attention)
        for name, layer in layers.items():
            if name not in layer_names:
                continue
            assert isinstance(layer.impl, AiterFlashAttentionImpl), (
                "Aiter Flash Attention Metadata Builder can only be used "
                "with Aiter Flash Attention Impl."
            )
            sliding_window_configs.add(layer.impl.sliding_window)

        while len(sliding_window_configs) > 0:
            sliding_window_config = sliding_window_configs.pop()
            if sliding_window_config is not None and sliding_window_config[0] != -1:
                assert self.aot_sliding_window is None, (
                    "Aiter Flash ATTENTION can only support one valid sliding window!"
                )
                self.aot_sliding_window = sliding_window_config

        self.extend_workspace = torch.empty(
            [2, _CP_TOKENS_PER_ITER_ROCM, self.num_heads_kv, self.headdim],
            dtype=self.model_config.dtype,
            device=device,
        )
        self.scale = torch.tensor([1.0], dtype=torch.float, device=self.device)