def __init__(
        self,
        config: MiniMaxConfig,
        model_config: ModelConfig | None = None,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        expert_num: int = 1,
        layer_id: int = None,
        linear_layer_id: int | None = None,
        prefix: str = "decoder",
    ) -> None:
        self._ilayer = layer_id
        self._irank = get_tensor_model_parallel_rank()
        self.prefix = prefix
        super().__init__()

        self.hidden_size = config.hidden_size
        self.expert_num = expert_num

        head_dim = getattr(config, "head_dim", None)
        if head_dim is None:
            head_dim = config.hidden_size // config.num_attention_heads
        rotary_dim = getattr(config, "rotary_dim", head_dim)
        config.rope_parameters["partial_rotary_factor"] = rotary_dim / head_dim
        if hasattr(config, "max_model_len") and isinstance(config.max_model_len, int):
            max_position_embeddings = min(
                config.max_position_embeddings, config.max_model_len
            )
        if config.attention_type == 0:
            use_headxdim = True
            hidden_inner = (
                head_dim * config.num_attention_heads
                if use_headxdim
                else config.hidden_size
            )
            self.self_attn = MiniMaxText01LinearAttention(
                hidden_size=self.hidden_size,
                hidden_inner_size=hidden_inner,
                num_heads=config.num_attention_heads,
                head_dim=head_dim,
                max_position=max_position_embeddings,
                block_size=config.block if hasattr(config, "block") else 256,
                num_hidden_layer=config.num_hidden_layers,
                model_config=model_config,
                cache_config=cache_config,
                quant_config=quant_config,
                layer_idx=self._ilayer,
                linear_layer_idx=linear_layer_id,
                prefix=prefix,
            )
        elif config.attention_type == 1:
            self.self_attn = MiniMaxText01Attention(
                hidden_size=self.hidden_size,
                num_heads=config.num_attention_heads,
                head_dim=head_dim,
                num_kv_heads=config.num_key_value_heads,
                max_position=max_position_embeddings,
                rope_parameters=config.rope_parameters,
                sliding_window=config.sliding_window,
                quant_config=quant_config,
                layer_idx=self._ilayer,
                cache_config=cache_config,
                prefix=prefix,
            )
        else:
            raise ValueError(
                f"Unsupported attention_type {self.config.attention_type}: "
                f"should be 0 (linear) or 1 (full)."
            )

        if expert_num == 1:
            self.mlp = MiniMaxText01MLP(
                hidden_size=self.hidden_size,
                intermediate_size=config.intermediate_size,
                quant_config=quant_config,
                layer_idx=self._ilayer,
                prefix=prefix,
            )
        else:
            self.block_sparse_moe = MiniMaxText01MoE(
                num_experts=expert_num,
                top_k=config.num_experts_per_tok,
                hidden_size=config.hidden_size,
                intermediate_size=config.intermediate_size,
                layer_idx=self._ilayer,
                quant_config=quant_config,
                prefix=prefix,
            )

        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(
            config.hidden_size, eps=config.rms_norm_eps
        )
        if config.attention_type == 0:
            self.layernorm_attention_alpha = getattr(
                config,
                "layernorm_linear_attention_alpha",
                getattr(config, "linear_attn_alpha_factor", 1),
            )
            self.layernorm_attention_beta = getattr(
                config,
                "layernorm_linear_attention_beta",
                getattr(config, "linear_attn_beta_factor", 1),
            )
        else:
            self.layernorm_attention_alpha = getattr(
                config,
                "layernorm_full_attention_alpha",
                getattr(config, "full_attn_alpha_factor", 1),
            )
            self.layernorm_attention_beta = getattr(
                config,
                "layernorm_full_attention_beta",
                getattr(config, "full_attn_beta_factor", 1),
            )
        self.layernorm_mlp_alpha = getattr(
            config, "layernorm_mlp_alpha", getattr(config, "mlp_alpha_factor", 1)
        )
        self.layernorm_mlp_beta = getattr(
            config, "layernorm_mlp_beta", getattr(config, "mlp_beta_factor", 1)
        )
        self.postnorm = getattr(config, "postnorm", False)
        self.shared_moe = False

        shared_intermediate = getattr(config, "shared_intermediate_size", 0)
        if isinstance(shared_intermediate, list):
            shared_intermediate = (
                shared_intermediate[layer_id]
                if layer_id < len(shared_intermediate)
                else 0
            )
        if shared_intermediate > 0:
            self.shared_moe = True
            self.shared_mlp = MiniMaxText01MLP(
                hidden_size=self.hidden_size,
                intermediate_size=shared_intermediate,
                quant_config=quant_config,
                layer_idx=self._ilayer,
                prefix=prefix,
            )
            self.coefficient = ReplicatedLinear(
                self.hidden_size,
                1,
                bias=False,
                quant_config=quant_config,
                params_dtype=torch.float32,
            )
            self.coefficient.weight.weight_loader = self.shared_moe_coefficient_loader
            self.shared_moe_mode = getattr(config, "shared_moe_mode", "softmax")
        return