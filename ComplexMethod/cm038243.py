def __init__(
        self,
        config: PretrainedConfig,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
        layer_id: int = -1,
        enable_eplb: bool = False,
    ) -> None:
        super().__init__()
        assert layer_id >= 0
        self.layer_id = layer_id
        self.hidden_size = config.hidden_size
        self.intermediate_size = (
            config.intermediate_size
            if isinstance(config.intermediate_size, int)
            else config.intermediate_size[layer_id]
        )
        max_position_embeddings = getattr(config, "max_position_embeddings", 8192)
        attention_bias = getattr(config, "attention_bias", False) or getattr(
            config, "bias", False
        )
        cla_factor = _get_cla_factor(config)
        attention_type = (
            AttentionType.ENCODER_DECODER
            if layer_id >= 0 and layer_id % cla_factor != 0
            else AttentionType.DECODER
        )
        if attention_type == AttentionType.DECODER:
            self.self_attn = HunYuanAttention(
                config=config,
                hidden_size=self.hidden_size,
                num_heads=config.num_attention_heads,
                num_kv_heads=getattr(
                    config, "num_key_value_heads", config.num_attention_heads
                ),
                max_position_embeddings=max_position_embeddings,
                quant_config=quant_config,
                bias=attention_bias,
                cache_config=cache_config,
                prefix=f"{prefix}.self_attn",
                layer_id=layer_id,
            )
        elif attention_type == AttentionType.ENCODER_DECODER:
            self.self_attn = HunYuanCrossAttention(
                config=config,
                hidden_size=self.hidden_size,
                num_heads=config.num_attention_heads,
                num_kv_heads=getattr(
                    config, "num_key_value_heads", config.num_attention_heads
                ),
                max_position_embeddings=max_position_embeddings,
                quant_config=quant_config,
                bias=attention_bias,
                cache_config=cache_config,
                prefix=f"{prefix}.self_attn",
                layer_id=layer_id,
            )
        else:
            raise RuntimeError(f"Unsupported attention type: {attention_type}")

        if _is_moe(config):
            self.mlp = HunYuanSparseMoeBlock(
                config=config,
                quant_config=quant_config,
                layer_id=layer_id,
                prefix=f"{prefix}.mlp",
                enable_eplb=enable_eplb,
            )
        else:
            self.mlp = HunYuanMLP(
                hidden_size=self.hidden_size,
                intermediate_size=self.intermediate_size,
                hidden_act=config.hidden_act,
                quant_config=quant_config,
                bias=getattr(config, "mlp_bias", False),
                prefix=f"{prefix}.mlp",
            )

        self.input_layernorm = RMSNorm(config.hidden_size, eps=config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(
            config.hidden_size, eps=config.rms_norm_eps
        )