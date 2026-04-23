def __init__(
        self,
        vllm_config: VllmConfig,
        config: FlashConfig,
        cache_config: CacheConfig | None = None,
        quant_config: QuantizationConfig | None = None,
        prefix: str = "",
        enable_eplb: bool = False,
    ) -> None:
        super().__init__()
        self.layer_idx = int(prefix.split(sep=".")[-1])
        self.hidden_size = config.hidden_size
        max_position_embeddings = getattr(config, "max_position_embeddings", 8192)

        # Dual attention structure
        self.self_attn = nn.ModuleList(
            [
                DeepseekV2MLAAttention(
                    vllm_config=vllm_config,
                    config=config,
                    hidden_size=self.hidden_size,
                    num_heads=config.num_attention_heads,
                    qk_nope_head_dim=config.qk_nope_head_dim,
                    qk_rope_head_dim=config.qk_rope_head_dim,
                    v_head_dim=config.v_head_dim,
                    q_lora_rank=(
                        config.q_lora_rank if hasattr(config, "q_lora_rank") else None
                    ),
                    kv_lora_rank=config.kv_lora_rank,
                    max_position_embeddings=max_position_embeddings,
                    cache_config=cache_config,
                    quant_config=None
                    if "self_attn" in getattr(config, "disable_quant_module", [])
                    else quant_config,
                    prefix=f"{prefix}.self_attn.{i}",
                )
                for i in range(2)
            ]
        )
        self.input_layernorm = nn.ModuleList(
            [RMSNorm(config.hidden_size, eps=config.rms_norm_eps) for i in range(2)]
        )
        self.post_attention_layernorm = nn.ModuleList(
            [RMSNorm(config.hidden_size, eps=config.rms_norm_eps) for i in range(2)]
        )

        # Dual MLP structure
        self.mlps = nn.ModuleList(
            [
                FlashMLP(
                    hidden_size=self.hidden_size,
                    intermediate_size=config.intermediate_size,
                    hidden_act=config.hidden_act,
                    quant_config=None
                    if "mlps" in getattr(config, "disable_quant_module", [])
                    else quant_config,
                    prefix=f"{prefix}.mlps.{i}",
                )
                for i in range(2)
            ]
        )

        self.mlp = LongcatMoe(
            config=config,
            num_experts=config.n_routed_experts
            if hasattr(config, "n_routed_experts")
            else config.num_experts[self.layer_idx],
            top_k=config.moe_topk
            if hasattr(config, "moe_topk")
            else config.num_experts_per_tok,
            hidden_size=config.hidden_size,
            intermediate_size=config.moe_intermediate_size,
            quant_config=quant_config,
            prefix=(f"{prefix}.mlp"),
        )