def __init__(
        self,
        config: TextConfig,
        rope_parameters: dict[str, Any],
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()
        self.hidden_size = config.hidden_size
        self.tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = config.num_attention_heads

        assert self.hidden_size % self.total_num_heads == 0
        assert self.total_num_heads % self.tp_size == 0

        self.num_heads = self.total_num_heads // self.tp_size
        self.total_num_kv_heads = config.num_key_value_heads
        if self.total_num_kv_heads >= self.tp_size:
            assert self.total_num_kv_heads % self.tp_size == 0
        else:
            assert self.tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // self.tp_size)
        self.head_dim = config.head_dim

        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.max_position_embeddings = config.max_position_embeddings
        self.rope_theta = config.rope_theta

        # Attention input projection. Projects x -> (q, k, v)
        self.qkv_proj = QKVParallelLinear(
            self.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=config.qkv_bias,
            quant_config=quant_config,
        )

        self.tp_rank: int | None = None
        self.k_norm: nn.Module | None = None
        self.q_norm: nn.Module | None = None
        self.qk_norm_type: str | None = None
        if config.use_qk_norm:
            k_norm_size = (
                self.head_dim
                if config.qk_norm_type == "qwen3"
                else self.total_num_kv_heads * self.head_dim
            )
            self.tp_rank = get_tensor_model_parallel_rank()
            self.k_norm = RMSNorm(k_norm_size, eps=config.layer_norm_eps)
            q_norm_size = (
                self.head_dim
                if config.qk_norm_type == "qwen3"
                else self.total_num_heads * self.head_dim
            )
            self.q_norm = RMSNorm(q_norm_size, eps=config.layer_norm_eps)
            self.qk_norm_type = config.qk_norm_type
        # Rotary embeddings. Rope scaling is only applied on full attention layers.
        layer_idx = extract_layer_index(prefix)
        if (
            config.rope_scaling_layers is not None
            and layer_idx not in config.rope_scaling_layers
        ):
            rope_theta = rope_parameters["rope_theta"]
            rope_parameters = {"rope_type": "default", "rope_theta": rope_theta}
        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=self.max_position_embeddings,
            rope_parameters=rope_parameters,
        )
        self.scaling = self.head_dim**-0.5
        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            prefix=f"{prefix}.attn",
        )

        # Attention output projection.
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            self.hidden_size,
            bias=False,
            quant_config=quant_config,
        )