def __init__(self, *, vllm_config: VllmConfig, prefix: str = ""):
        super().__init__()
        self.config = vllm_config.model_config.hf_config
        assert isinstance(self.config, (Olmo2Config, Olmo3Config))

        hidden_size = self.config.hidden_size
        self.tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = self.config.num_attention_heads

        assert hidden_size % self.total_num_heads == 0
        assert self.total_num_heads % self.tp_size == 0

        self.num_heads = self.total_num_heads // self.tp_size
        self.total_num_kv_heads = (
            self.config.num_key_value_heads or self.total_num_heads
        )
        if self.total_num_kv_heads >= self.tp_size:
            assert self.total_num_kv_heads % self.tp_size == 0
        else:
            assert self.tp_size % self.total_num_kv_heads == 0

        self.num_kv_heads = max(1, self.total_num_kv_heads // self.tp_size)
        self.head_dim = hidden_size // self.total_num_heads
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.max_position_embeddings = self.config.max_position_embeddings

        # Attention input projection. Projects x -> (q, k, v)
        self.qkv_proj = QKVParallelLinear(
            hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=False,
            quant_config=vllm_config.quant_config,
            prefix=f"{prefix}.qkv_proj",
        )

        self.tp_rank = get_tensor_model_parallel_rank()
        self.k_norm = RMSNorm(
            self.total_num_kv_heads * self.head_dim,
            eps=self.config.rms_norm_eps,
        )
        self.q_norm = RMSNorm(self.config.hidden_size, eps=self.config.rms_norm_eps)

        self.scaling = self.head_dim**-0.5

        layer_idx = extract_layer_index(prefix)
        sliding_window = None
        if (
            layer_types := getattr(self.config, "layer_types", None)
        ) is not None and layer_types[layer_idx] == "sliding_attention":
            sliding_window = self.config.sliding_window

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=vllm_config.cache_config,
            quant_config=vllm_config.quant_config,
            per_layer_sliding_window=sliding_window,
            prefix=f"{prefix}.attn",
        )

        # Rotary embeddings. Rope scaling is only applied on full attention layers.
        if sliding_window is None:
            rope_parameters = self.config.rope_parameters
        else:
            rope_theta = self.config.rope_parameters["rope_theta"]
            rope_parameters = {"rope_type": "default", "rope_theta": rope_theta}
        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=self.max_position_embeddings,
            rope_parameters=rope_parameters,
        )

        # Attention output projection.
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            hidden_size,
            bias=False,
            quant_config=vllm_config.quant_config,
            prefix=f"{prefix}.o_proj",
        )