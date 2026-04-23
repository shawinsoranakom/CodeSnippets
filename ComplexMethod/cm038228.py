def __init__(
        self,
        hidden_size: int,
        num_heads: int,
        num_kv_heads: int,
        max_position: int = 4096 * 32,
        head_dim: int | None = None,
        rms_norm_eps: float = 1e-06,
        qkv_bias: bool = False,
        rope_theta: float | list[float] | None = 10000,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        rope_scaling: dict[str, Any] | None = None,
        prefix: str = "",
        attn_type: str = AttentionType.DECODER,
        # Step3p5 specific args
        sliding_window: int | None = None,
        use_head_wise_attn_gate: bool = False,
        layer_types: list = None,
        use_rope_layers: list = None,
        yarn_only_types: list = None,
        swa_num_attention_heads: int | None = None,
        partial_rotary_factor: float = 1.0,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.total_num_heads = num_heads
        tp_size = get_tensor_model_parallel_world_size()
        self.layer_idx = extract_layer_index(prefix)
        if layer_types:
            enable_sliding_window = layer_types[self.layer_idx] == "sliding_attention"
        else:
            enable_sliding_window = self.layer_idx % 2 == 0
        if yarn_only_types and layer_types[self.layer_idx] not in yarn_only_types:
            rope_scaling = None

        if sliding_window is not None and enable_sliding_window:
            sliding_window = sliding_window
            if swa_num_attention_heads is not None:
                num_heads = swa_num_attention_heads
                self.total_num_heads = swa_num_attention_heads
        else:
            sliding_window = None

        if isinstance(rope_theta, list):
            rope_theta = rope_theta[self.layer_idx]

        self.rank = get_tensor_model_parallel_rank()
        self.partial_rotary_factor = partial_rotary_factor
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
        self.head_dim = head_dim or hidden_size // self.total_num_heads
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.scaling = self.head_dim**-0.5
        self.rope_theta = rope_theta
        self.qkv_proj = QKVParallelLinear(
            hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=qkv_bias,
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

        if rope_scaling is not None and not isinstance(rope_scaling, dict):
            raise ValueError("rope_scaling must be a dict for Step3p5Attention.")

        rope_parameters: dict[str, Any] = (
            dict(rope_scaling) if rope_scaling is not None else {}
        )
        rope_parameters.setdefault("rope_type", "default")
        rope_parameters["rope_theta"] = self.rope_theta
        rope_parameters["partial_rotary_factor"] = partial_rotary_factor

        self.rotary_emb = get_rope(
            head_size=self.head_dim,
            max_position=max_position,
            rope_parameters=rope_parameters,
        )

        self.q_norm = GemmaRMSNorm(self.head_dim, rms_norm_eps)
        self.k_norm = GemmaRMSNorm(self.head_dim, rms_norm_eps)
        self.use_head_wise_attn_gate = use_head_wise_attn_gate
        if use_head_wise_attn_gate:
            self.g_proj = ColumnParallelLinear(
                hidden_size,
                self.total_num_heads,
                bias=False,
                quant_config=quant_config,
                prefix=f"{prefix}.g_proj",
            )

        self.use_rope = True
        if use_rope_layers:
            self.use_rope = use_rope_layers[self.layer_idx]

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            prefix=f"{prefix}.attn",
            per_layer_sliding_window=sliding_window,
            attn_type=attn_type,
        )

        self.max_position_embeddings = max_position
        assert self.partial_rotary_factor == 1 or self.partial_rotary_factor == 0.5
        self.rotary_dim = (
            self.head_dim if self.partial_rotary_factor == 1 else self.head_dim // 2
        )