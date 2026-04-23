def __init__(
        self,
        vllm_config: VllmConfig,
        prefix: str = "",
    ) -> None:
        super().__init__()
        config = vllm_config.model_config.hf_config
        self.hidden_size = config.hidden_size
        layer_idx = extract_layer_index(prefix)
        self.layer_idx = layer_idx
        cache_config = vllm_config.cache_config
        quant_config = vllm_config.quant_config
        if cache_config is not None:
            cache_config.sliding_window = None
        if config.att_impl_type == "GQA":
            num_attention_heads = None
            num_attention_groups = None
            head_dim = None
            if (
                getattr(config, "attention_other_setting", None)
                and getattr(config, "layer_types", [])
                and config.layer_types[layer_idx]
                == config.attention_other_setting["attention_type"]
            ):
                num_attention_heads = config.attention_other_setting[
                    "num_attention_heads"
                ]
                num_attention_groups = config.attention_other_setting[
                    "num_attention_groups"
                ]
                head_dim = config.attention_other_setting["head_dim"]
            partial_rotary_factors = getattr(config, "partial_rotary_factors", [])
            self.self_attn = Step3p5Attention(
                hidden_size=self.hidden_size,
                num_heads=num_attention_heads
                if num_attention_heads
                else config.num_attention_heads,
                max_position=config.max_position_embeddings,
                num_kv_heads=num_attention_groups
                if num_attention_groups
                else config.num_attention_groups,
                rope_theta=config.rope_theta,
                rms_norm_eps=config.rms_norm_eps,
                qkv_bias=getattr(config, "attention_bias", False),
                head_dim=head_dim if head_dim else getattr(config, "head_dim", None),
                cache_config=cache_config,
                quant_config=quant_config,
                rope_scaling=getattr(config, "rope_scaling", None),
                sliding_window=getattr(config, "sliding_window", None),
                use_head_wise_attn_gate=getattr(
                    config, "use_head_wise_attn_gate", False
                ),
                layer_types=getattr(config, "layer_types", []),
                use_rope_layers=getattr(config, "use_rope_layers", []),
                yarn_only_types=getattr(config, "yarn_only_types", []),
                partial_rotary_factor=partial_rotary_factors[layer_idx]
                if partial_rotary_factors
                else 1.0,
                prefix=f"{prefix}.self_attn",
            )
        else:
            raise ValueError(
                f"Unsupported attention implementation: {config.att_impl_type}"
            )
        self.use_moe = False
        self.tp_group = get_tp_group()
        self.use_fused_all_reduce = (
            get_tensor_model_parallel_world_size() > 1
            and get_dp_group().world_size == 1
        )
        if self.use_fused_all_reduce:
            logger.warning_once("Enable custom fused all reduce...")
        else:
            logger.warning_once("Disable custom fused all reduce...")

        moe_layers_enum = getattr(config, "moe_layers_enum", None)
        if moe_layers_enum is not None:
            moe_layers_idx = [int(i) for i in moe_layers_enum.strip().split(",")]
        else:
            moe_layers_idx = [i for i in range(1, config.num_hidden_layers)]
        if layer_idx in moe_layers_idx:
            self.moe = FusedMoEBlock(
                vllm_config,
                prefix=f"{prefix}.moe",
            )
            self.use_moe = True
        else:
            self.mlp = Step3p5MLP(
                config=config,
                hidden_size=config.hidden_size,
                intermediate_size=config.intermediate_size,
                hidden_act="silu",
                quant_config=quant_config,
                reduce_results=True,
                prefix=f"{prefix}.mlp",
            )
        self.input_layernorm = GemmaRMSNorm(config.hidden_size, config.rms_norm_eps)
        self.post_attention_layernorm = GemmaRMSNorm(
            config.hidden_size, config.rms_norm_eps
        )
        self.prefix = prefix