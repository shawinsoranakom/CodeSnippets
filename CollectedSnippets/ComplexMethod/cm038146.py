def __init__(
        self,
        config: PretrainedConfig,
        quant_config: QuantizationConfig | None = None,
        layer_id: int = 0,
        prefix: str = "linear_attn",
        model_config: ModelConfig | None = None,
        cache_config: CacheConfig | None = None,
    ):
        super().__init__()

        self.layer_id = layer_id
        self.hidden_size = config.hidden_size
        self.total_num_heads = config.num_attention_heads
        self.total_kv_heads = config.num_attention_heads  # MHA
        self.tp_size = get_tensor_model_parallel_world_size()
        self.tp_rank = get_tensor_model_parallel_rank()
        self.model_config = model_config
        self.cache_config = cache_config
        self.prefix = prefix

        self.head_dim = (
            config.head_dim
            if hasattr(config, "head_dim")
            else config.hidden_size // self.total_num_heads
        )

        self.hidden_inner_size = self.head_dim * self.total_num_heads
        self.scaling = self.head_dim**-0.5

        assert self.total_num_heads % self.tp_size == 0
        self.tp_heads = self.total_num_heads // self.tp_size

        self.max_position_embeddings = config.max_position_embeddings
        self.rope_theta = getattr(config, "rope_theta", 600000)

        self.tp_kv_heads = self.total_kv_heads // self.tp_size
        self.q_size_per_rank = self.head_dim * self.tp_heads
        self.kv_size_per_rank = self.head_dim * self.tp_kv_heads

        self.use_qk_norm = getattr(config, "use_qk_norm", False)
        self.linear_backend = "minimax"
        self.linear_scale = self.linear_backend == "minimax"
        self.linear_rope = getattr(config, "linear_rope", True)
        if hasattr(config, "use_linear_silu"):
            self.linear_silu = config.use_linear_silu
        elif hasattr(config, "linear_silu"):
            self.linear_silu = config.linear_silu
        else:
            self.linear_silu = False

        # Block size for lightning attention
        self.BLOCK = getattr(config, "block", 256)

        self.query_key_value = QKVParallelLinear(
            self.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_heads,  # MHA: kv_heads = num_heads
            bias=(config.use_bias or config.use_qkv_bias),
            quant_config=quant_config,
            prefix=f"{prefix}.query_key_value",
        )

        if self.use_qk_norm:
            self.query_layernorm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
            self.key_layernorm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)

        self.g_proj = ColumnParallelLinear(
            self.hidden_size,
            self.hidden_inner_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.g_proj",
        )
        self.dense = RowParallelLinear(
            self.hidden_inner_size,
            self.hidden_size,
            bias=config.use_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.dense",
            reduce_results=True,
        )

        self.group_norm_size = getattr(config, "group_norm_size", 1)
        self.rms_norm_eps = float(getattr(config, "rms_norm_eps", 1e-5))
        assert self.tp_size <= self.group_norm_size, (
            "tp_size must be <= group_norm_size for local rms norm"
        )
        assert self.group_norm_size % self.tp_size == 0, (
            "group_norm_size must be divisible by tp_size"
        )

        # When group_norm_size == 1, group_size equals hidden_size // tp_size
        self.g_norm = BailingGroupRMSNormGate(
            hidden_size=self.hidden_inner_size // self.tp_size,
            eps=self.rms_norm_eps,
            group_size=(
                self.hidden_inner_size // self.group_norm_size
                if self.group_norm_size > 1
                else self.hidden_inner_size // self.tp_size
            ),
        )

        # use fp32 rotary embedding
        rope_parameters = _build_rope_parameters(config)

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=self.max_position_embeddings,
            is_neox_style=True,
            dtype=torch.float32,
            rope_parameters=rope_parameters or None,
        )

        # Build slope tensor for linear attention decay
        num_hidden_layers = config.num_hidden_layers
        slope_rate = MiniMaxText01LinearAttention._build_slope_tensor(
            self.total_num_heads
        )
        if num_hidden_layers <= 1:
            self.slope_rate = slope_rate * (1 + 1e-5)
        else:
            self.slope_rate = slope_rate * (
                1 - layer_id / (num_hidden_layers - 1) + 1e-5
            )
        self.tp_slope = self.slope_rate[
            self.tp_rank * self.tp_heads : (self.tp_rank + 1) * self.tp_heads
        ].contiguous()

        # Register for compilation
        compilation_config = get_current_vllm_config().compilation_config
        if prefix in compilation_config.static_forward_context:
            raise ValueError(f"Duplicate layer name: {prefix}")
        compilation_config.static_forward_context[prefix] = self