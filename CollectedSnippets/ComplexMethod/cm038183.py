def __init__(self, *, vllm_config: VllmConfig, prefix: str = "model"):
        super().__init__()
        config: IsaacConfig = vllm_config.model_config.hf_config
        quant_config = vllm_config.quant_config
        self.config = config

        head_dim = config.head_dim
        calculated_mrope_section = [
            head_dim // 4,  # 2x more for temporal dim
            head_dim // 8,
            head_dim // 8,
        ]

        self.vision_token_id = _resolve_vision_token_id(
            vllm_config.model_config, config.vision_token
        )
        config.image_token_id = self.vision_token_id

        text_cfg = getattr(config, "text_config", None)
        target_cfg = (
            text_cfg
            if text_cfg is not None and not isinstance(text_cfg, dict)
            else config
        )

        rope_scaling = getattr(target_cfg, "rope_scaling", None)
        if rope_scaling is None and target_cfg is config:
            rope_scaling = getattr(config, "_rope_scaling", None)

        patch_rope_parameters(target_cfg)
        rope_parameters = target_cfg.rope_parameters
        rope_parameters["mrope_section"] = calculated_mrope_section
        if rope_scaling is not None and "mrope_interleaved" in rope_scaling:
            rope_parameters.setdefault(
                "mrope_interleaved", rope_scaling["mrope_interleaved"]
            )
        target_cfg.rope_parameters = rope_parameters

        with self._mark_language_model(vllm_config):
            self.language_model = init_vllm_registered_model(
                vllm_config=vllm_config,
                architectures=["Qwen3ForCausalLM"],
                prefix=maybe_prefix(prefix, "language_model"),
            )

        self.make_empty_intermediate_tensors = (
            self.language_model.make_empty_intermediate_tensors
        )

        vision_cfg = config.vision_config
        if vision_cfg is None:
            raise ValueError("IsaacConfig should always have vision_config")
        attn_impl = (
            config.vision_attn_implementation
            if config.vision_attn_implementation is not None
            else getattr(config, "_attn_implementation", None)
        )
        if attn_impl is not None:
            vision_cfg._attn_implementation = attn_impl

        hidden_dim = vision_cfg.hidden_size * (vision_cfg.pixel_shuffle_scale_factor**2)

        with self._mark_tower_model(vllm_config, "image"):
            self.vision_embedding = IsaacVisionEmbedding(
                vision_cfg=vision_cfg,
                hidden_dim=hidden_dim,
                output_dim=config.hidden_size,
                quant_config=quant_config,
                prefix=maybe_prefix(prefix, "vision_embedding"),
            )