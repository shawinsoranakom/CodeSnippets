def __init__(
        self,
        config: PretrainedConfig,
        hidden_size: int,
        num_heads: int,
        num_kv_heads: int,
        max_position: int = 4096 * 32,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
        attn_type: str = AttentionType.DECODER,
        dual_chunk_attention_config: dict[str, Any] | None = None,
        layer_idx: int = 0,
    ) -> None:
        super().__init__()
        self.layer_idx = layer_idx
        self.hidden_size = hidden_size
        tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = num_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
        self.total_num_kv_heads = num_kv_heads
        if self.total_num_kv_heads >= tp_size:
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_kv_heads % tp_size == 0
        else:
            # Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)
        self.head_dim = hidden_size // self.total_num_heads
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.scaling = self.head_dim**-0.5
        self.dual_chunk_attention_config = dual_chunk_attention_config

        # Get loop_num from config, default to 2 if not specified
        self.loop_num = getattr(config, "loop_num", 2)

        self.loop_window_size = getattr(config, "loop_window_size", 64)

        # Use total number of hidden layers instead of hardcoded 24
        total_layers = config.num_hidden_layers

        self.qkv_proj = QKVParallelLinear(
            hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            hidden_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=max_position,
            rope_parameters=config.rope_parameters,
            dual_chunk_attention_config=dual_chunk_attention_config,
        )
        self.attn = nn.ModuleList()

        base_cache_config = cache_config

        for loop_idx in range(self.loop_num):
            base_layer_idx = extract_layer_index(prefix)
            unique_layer_idx = loop_idx * total_layers + base_layer_idx

            unique_prefix = prefix.replace(
                f"layers.{base_layer_idx}", f"layers.{unique_layer_idx}"
            )

            if loop_idx == 0:
                loop_cache_config = cache_config
            else:
                if base_cache_config is not None:
                    loop_cache_config = replace(
                        base_cache_config,
                        sliding_window=self.loop_window_size,
                    )
                else:
                    loop_cache_config = CacheConfig(
                        sliding_window=self.loop_window_size,
                        cache_dtype="auto",
                    )

            self.attn.append(
                Attention(
                    self.num_heads,
                    self.head_dim,
                    self.scaling,
                    num_kv_heads=self.num_kv_heads,
                    cache_config=loop_cache_config,
                    quant_config=quant_config,
                    attn_type=attn_type,
                    prefix=f"{unique_prefix}.attn",
                    **{
                        "layer_idx": unique_layer_idx,
                        "dual_chunk_attention_config": dual_chunk_attention_config,
                    }
                    if dual_chunk_attention_config and loop_idx == 0
                    else {},
                )
            )