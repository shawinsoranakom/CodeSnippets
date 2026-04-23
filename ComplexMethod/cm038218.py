def __init__(
        self,
        config,
        hidden_size: int,
        num_heads: int,
        num_kv_heads: int,
        head_dim: int,
        max_position_embeddings: int,
        use_k_eq_v: bool = False,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        attn_logits_soft_cap: float | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()
        self.config = config
        self.hidden_size = hidden_size
        self.use_k_eq_v = use_k_eq_v

        tp_size = get_tensor_model_parallel_world_size()
        self.tp_rank = get_tensor_model_parallel_rank()
        self.total_num_heads = num_heads
        assert self.total_num_heads % tp_size == 0
        self.num_heads = self.total_num_heads // tp_size
        self.total_num_kv_heads = num_kv_heads
        if self.total_num_kv_heads >= tp_size:
            assert self.total_num_kv_heads % tp_size == 0
        else:
            assert tp_size % self.total_num_kv_heads == 0
        self.num_kv_heads = max(1, self.total_num_kv_heads // tp_size)
        self.head_dim = head_dim
        self.q_size = self.num_heads * self.head_dim
        self.kv_size = self.num_kv_heads * self.head_dim
        # Gemma4 uses scaling=1.0.
        # Unlike Gemma2/3, query_pre_attn_scalar is NOT used here;
        # Q/K norms with learnable weights handle scaling implicitly.
        self.scaling = 1.0

        # QKVParallelLinear handles GQA correctly for all layer types.
        # k_eq_v layers load K weights into both K and V slots via
        # _weight_iterator remapping — no structural difference needed.
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

        # Q/K norms: output = norm(x) * weight (learnable per-head scale)
        self.q_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        self.k_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps)
        # V norm: no learnable scale (pure normalization only)
        self.v_norm = RMSNorm(self.head_dim, eps=config.rms_norm_eps, has_weight=False)

        # Determine layer type and sliding window
        layer_idx = extract_layer_index(prefix)
        layer_type = config.layer_types[layer_idx]
        self.is_sliding = layer_type == "sliding_attention"
        sliding_window = config.sliding_window if self.is_sliding else None

        # Initialize RoPE based on layer type.
        # Gemma4 uses different RoPE parameters for sliding vs full attention.
        if layer_type in config.rope_parameters:
            # Per-layer-type rope config (dict format).
            # rope_parameters already contains the correct
            # partial_rotary_factor per layer type (1.0 for full
            # attention, 1.0 for sliding). Do NOT override with
            # global_partial_rotary_factor — that config key is
            # not needed for Gemma4 — config uses per-layer rope_parameters.
            rope_parameters = dict(config.rope_parameters[layer_type])
        else:
            # Legacy config format fallback.
            rope_parameters = dict(config.rope_parameters.copy())
            if self.is_sliding:
                rope_parameters["rope_theta"] = getattr(
                    config, "rope_local_base_freq", 10000.0
                )

        # KV sharing: layers in the last `num_kv_shared_layers` share KV
        # cache with earlier layers of the same type.
        kv_sharing_target_layer_name = None
        self.is_kv_shared_layer = False
        num_kv_shared_layers = getattr(config, "num_kv_shared_layers", 0)
        if num_kv_shared_layers > 0:
            first_kv_shared_layer_idx = config.num_hidden_layers - num_kv_shared_layers
            if layer_idx >= first_kv_shared_layer_idx:
                self.is_kv_shared_layer = True
                # Find the last non-shared layer of the same attention type
                prev_layers = config.layer_types[:first_kv_shared_layer_idx]
                current_layer_type = config.layer_types[layer_idx]
                kv_shared_layer_index = (
                    len(prev_layers) - 1 - prev_layers[::-1].index(current_layer_type)
                )
                if kv_shared_layer_index >= 0:
                    if ".layers." in prefix:
                        param_name_before_layers = prefix.split(".layers.")[0]
                    else:
                        raise ValueError(
                            "Unexpected prefix format for Gemma4Attention: "
                            f"'{prefix}'. Expected to contain '.layers.'."
                        )
                    kv_sharing_target_layer_name = (
                        f"{param_name_before_layers}.layers."
                        f"{kv_shared_layer_index}.self_attn.attn"
                    )

        self.rotary_emb = get_rope(
            self.head_dim,
            max_position=max_position_embeddings,
            rope_parameters=rope_parameters,
            is_neox_style=True,
        )

        self.attn = Attention(
            self.num_heads,
            self.head_dim,
            self.scaling,
            num_kv_heads=self.num_kv_heads,
            cache_config=cache_config,
            quant_config=quant_config,
            logits_soft_cap=attn_logits_soft_cap,
            per_layer_sliding_window=sliding_window,
            kv_sharing_target_layer_name=kv_sharing_target_layer_name,
            prefix=f"{prefix}.attn",
        )