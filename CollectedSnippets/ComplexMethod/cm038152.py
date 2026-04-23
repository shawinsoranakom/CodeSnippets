def __init__(
        self,
        config: PretrainedConfig,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        reduce_results: bool = True,
        prefix: str = "",
    ):
        super().__init__()
        self.hidden_size = config.hidden_size
        self.total_num_heads = config.num_attention_heads
        self.total_kv_heads = config.num_key_value_heads
        tp_size = get_tensor_model_parallel_world_size()

        assert self.total_num_heads % tp_size == 0
        assert self.total_num_heads >= self.total_kv_heads

        self.num_heads = self.total_num_heads // tp_size
        self.head_dim = config.head_dim or (self.hidden_size // self.total_num_heads)
        self.q_size_per_rank = self.head_dim * self.num_heads
        self.num_kv_heads = max(1, self.total_kv_heads // tp_size)
        self.kv_size_per_rank = self.num_kv_heads * self.head_dim
        self.scale = self.head_dim**-0.5
        self.use_qk_norm = getattr(config, "use_qk_norm", False)
        self.use_rmsnorm = getattr(config, "use_rmsnorm", False)

        self.query_key_value = QKVParallelLinear(
            self.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_kv_heads,
            bias=(config.use_bias or config.use_qkv_bias),
            quant_config=quant_config,
            prefix=f"{prefix}.query_key_value",
        )

        if self.use_qk_norm:
            self.query_layernorm = (
                RMSNorm(self.head_dim, eps=config.rms_norm_eps)
                if self.use_rmsnorm
                else nn.LayerNorm(self.head_dim, eps=1e-6)
            )
            self.key_layernorm = (
                RMSNorm(self.head_dim, eps=config.rms_norm_eps)
                if self.use_rmsnorm
                else nn.LayerNorm(self.head_dim, eps=1e-6)
            )

        self.dense = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            self.hidden_size,
            bias=config.use_bias,
            quant_config=quant_config,
            reduce_results=reduce_results,
            prefix=f"{prefix}.dense",
        )

        rotary_dim = getattr(config, "rotary_dim", self.head_dim)
        config.rope_parameters["partial_rotary_factor"] = rotary_dim / self.head_dim

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=config.max_position_embeddings,
            rope_parameters=config.rope_parameters,
            is_neox_style=True,
        )

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scale,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            prefix=f"{prefix}.attn",
        )