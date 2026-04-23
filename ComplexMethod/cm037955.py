def __init__(
        self,
        config: CohereConfig | Cohere2Config,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ):
        super().__init__()
        tp_size = get_tensor_model_parallel_world_size()
        self.config = config
        self.attention_dropout = config.attention_dropout
        self.hidden_size = config.hidden_size
        self.total_num_heads = config.num_attention_heads
        self.num_heads = self.total_num_heads // tp_size
        self.head_dim = self.hidden_size // self.total_num_heads
        self.total_num_kv_heads = config.num_key_value_heads
        if self.total_num_kv_heads >= tp_size:
            # Number of KV heads is greater than TP size, so we partition
            # the KV heads across multiple tensor parallel GPUs.
            assert self.total_num_kv_heads % tp_size == 0
        else:
            # Number of KV heads is less than TP size, so we replicate
            # the KV heads across multiple tensor parallel GPUs.
            assert tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.scaling = self.head_dim**-0.5
        self.max_position_embeddings = getattr(
            config, "model_max_length", None
        ) or getattr(config, "max_position_embeddings", 8192)
        self.use_qk_norm = getattr(config, "use_qk_norm", False)
        self.qkv_proj = QKVParallelLinear(
            self.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            self.hidden_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )
        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=self.max_position_embeddings,
            rope_parameters=config.rope_parameters,
            is_neox_style=False,
        )

        # Model v2 has interleaved sliding windows, v1 does not
        self.v1 = isinstance(config, CohereConfig)

        self.sliding_window = None
        if not self.v1:
            layer_idx = extract_layer_index(prefix)
            if config.layer_types[layer_idx] == "sliding_attention":
                self.sliding_window = config.sliding_window

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            per_layer_sliding_window=self.sliding_window,
            prefix=f"{prefix}.attn",
        )
        if self.use_qk_norm:
            self.q_norm = LayerNorm(
                param_shape=(self.num_heads, self.head_dim), eps=config.layer_norm_eps
            )
            self.k_norm = LayerNorm(
                param_shape=(self.num_kv_heads, self.head_dim),
                eps=config.layer_norm_eps,
            )