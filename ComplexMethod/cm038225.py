def __init__(
        self,
        config: Gemma3nTextConfig,
        hidden_size: int,
        num_heads: int,
        num_kv_heads: int,
        head_dim: int,
        max_position_embeddings: int,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()
        self.config = config
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
        self.head_dim = head_dim
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim

        self.qkv_proj = QKVParallelLinear(
            hidden_size,
            self.head_dim,
            self.total_num_heads,
            self.total_num_kv_heads,
            bias=config.attention_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.qkv_proj",
        )
        self.o_proj = RowParallelLinear(
            self.total_num_heads * self.head_dim,
            hidden_size,
            bias=config.attention_bias,
            quant_config=quant_config,
            prefix=f"{prefix}.o_proj",
        )
        self.q_norm = RMSNorm(hidden_size=self.head_dim, eps=config.rms_norm_eps)
        self.k_norm = RMSNorm(hidden_size=self.head_dim, eps=config.rms_norm_eps)
        self.v_norm = RMSNorm(
            hidden_size=self.head_dim, eps=config.rms_norm_eps, has_weight=False
        )

        layer_idx = extract_layer_index(prefix)
        layer_type = config.layer_types[layer_idx]
        is_sliding = layer_type == "sliding_attention"
        self.sliding_window = config.sliding_window if is_sliding else None

        # Initialize the rotary embedding.
        if layer_type in config.rope_parameters:
            # Transformers v5 rope config.
            rope_parameters = config.rope_parameters[layer_type]
        else:
            # Transformers v4 rope config.
            # Global attention. Use the values in config.json.
            rope_parameters = config.rope_parameters.copy()
            # Local attention. Override the values in config.json.
            if is_sliding:
                rope_parameters["rope_theta"] = config.rope_local_base_freq

        first_kv_shared_layer_idx = (
            config.num_hidden_layers - config.num_kv_shared_layers
        )
        self.is_kv_shared = layer_idx >= first_kv_shared_layer_idx

        kv_sharing_target_layer_name = None
        if self.is_kv_shared:
            # Last full attention layer is 1 before sharing
            # Last sliding attention layer is 2 before sharing
            offset = 2 if self.sliding_window is not None else 1
            kv_shared_layer_index = first_kv_shared_layer_idx - offset
            if kv_shared_layer_index >= 0:
                # Different model wrappers expose layer parameters under
                # different parent attributes.
                # For example:
                #   - Gemma3nForCausalLM → parameters live under "model.layers"
                #   - Gemma3nForConditionalGeneration →
                #     under "language_model.model.layers"
                # This logic extracts the portion of the parameter name
                # *before* ".layers."
                # so downstream code can consistently reference the correct
                # model root regardless of which wrapper class was used.
                if ".layers." in prefix:
                    param_name_before_layers = prefix.split(".layers.")[0]
                else:
                    raise ValueError(
                        "Unexpected prefix format for Gemma3nAttention: "
                        f"'{prefix}'. The prefix is expected to contain "
                        "'.layers.' to correctly determine the KV sharing "
                        "target layer."
                    )
                # Only the greater layer is required to specify sharing.
                kv_sharing_target_layer_name = f"{param_name_before_layers}.layers.{kv_shared_layer_index}.self_attn.attn"  # noqa: E501

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=max_position_embeddings,
            rope_parameters=rope_parameters,
            is_neox_style=True,
        )

        self.attn = Attention(
            num_heads=self.num_heads,
            head_size=self.head_dim,
            scale=1.0,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            per_layer_sliding_window=self.sliding_window,
            kv_sharing_target_layer_name=kv_sharing_target_layer_name,
            prefix=f"{prefix}.attn",
        )