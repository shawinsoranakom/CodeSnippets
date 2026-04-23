def __init__(self, *, vllm_config: VllmConfig, prefix: str = "", **kwargs) -> None:
        super().__init__()
        config = vllm_config.model_config.hf_config
        quant_config = vllm_config.quant_config

        self.hidden_size = config.hidden_size
        tp_size = get_tensor_model_parallel_world_size()
        self.total_num_heads = config.num_attention_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
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
        self.head_dim = config.head_dim
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        self.scaling = self.head_dim**-0.5

        self.qkv_proj = QKVParallelLinear(
            config.hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            config.hidden_size,
            bias=False,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )

        layer_idx = extract_layer_index(prefix)
        layer_type = config.layer_types[layer_idx]
        is_sliding = layer_type == "sliding_attention"

        # Initialize the rotary embedding.
        if layer_type in config.rope_parameters:
            # Transformers v5 rope config.
            rope_parameters = config.rope_parameters[layer_type]
        else:
            # Transformers v4 rope config.
            # Global attention. Use the values in config.json.
            rope_parameters = config.rope_parameters
            # Local attention. Override the values in config.json.
            if is_sliding:
                rope_parameters = dict(
                    rope_type="default", rope_theta=config.rope_local_theta
                )
        max_position = config.max_position_embeddings
        if hasattr(vllm_config.model_config, "max_model_len") and isinstance(
            vllm_config.model_config.max_model_len, int
        ):
            max_position = min(max_position, vllm_config.model_config.max_model_len)

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=max_position,
            rope_parameters=rope_parameters,
        )
        self.q_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        set_weight_attrs(
            self.q_norm.weight, {"weight_loader": rms_norm_weight_loader(offset=1.0)}
        )
        self.k_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        set_weight_attrs(
            self.k_norm.weight, {"weight_loader": rms_norm_weight_loader(offset=1.0)}
        )
        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=vllm_config.cache_config,
            per_layer_sliding_window=config.interleaved_sliding_window[layer_idx],
            prefix=f"{prefix}.attn",
        )