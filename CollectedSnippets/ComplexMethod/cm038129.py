def __init__(
        self,
        config,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()

        self.hidden_size = config.hidden_size
        self.num_heads = config.num_attention_heads
        self.num_kv_heads = config.num_key_value_heads
        self.head_dim = config.head_dim or (self.hidden_size // self.num_heads)
        self.use_qk_norm: bool = getattr(config, "use_qk_norm", False)

        tp_size = get_tensor_model_parallel_world_size()
        assert self.num_heads % tp_size == 0, (
            f"num_attention_heads ({self.num_heads}) must be divisible "
            f"by tensor-parallel world size ({tp_size})."
        )
        assert self.num_kv_heads % tp_size == 0, (
            f"num_key_value_heads ({self.num_kv_heads}) must be divisible "
            f"by tensor-parallel world size ({tp_size})."
        )
        self.num_local_heads = self.num_heads // tp_size
        self.num_local_kv_heads = self.num_kv_heads // tp_size

        # Sizes after TP split (used in forward to split qkv output)
        self.q_size_local = self.num_local_heads * self.head_dim
        self.kv_size_local = self.num_local_kv_heads * self.head_dim

        self.scaling = self.head_dim**-0.5

        self.qkv_proj = QKVParallelLinear(
            hidden_size=self.hidden_size,
            head_size=self.head_dim,
            total_num_heads=self.num_heads,
            total_num_kv_heads=self.num_kv_heads,
            bias=getattr(config, "use_qkv_bias", False),
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )

        self.o_proj = RowParallelLinear(
            input_size=self.num_heads * self.head_dim,
            output_size=self.hidden_size,
            bias=getattr(config, "use_bias", False),
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        if self.use_qk_norm:
            self.q_layernorm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
            self.k_layernorm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)

        # `partial_rotary_factor` defaults to 1.0 (full RoPE) if not in config
        partial_rotary_factor: float = getattr(config, "partial_rotary_factor", 1.0)
        rope_dim = int(self.head_dim * partial_rotary_factor)

        rope_parameters: dict = {
            "rope_type": "default",
            "base": config.rope_theta,
        }
        if config.rope_scaling is not None:
            rope_parameters.update(config.rope_scaling)
            # Normalise key: some checkpoints use "type", vLLM wants "rope_type"
            if "type" in rope_parameters and "rope_type" not in rope_parameters:
                rope_parameters["rope_type"] = rope_parameters.pop("type")

        self.rotary_emb = get_rope(
            rope_dim,
            max_position=config.max_position_embeddings,
            rope_parameters=rope_parameters,
            is_neox_style=True,
        )

        self.attn = Attention(
            num_heads=self.num_local_heads,
            head_size=self.head_dim,
            scale=self.scaling,
            num_kv_heads=self.num_local_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            prefix=f"{prefix}.attn",
        )