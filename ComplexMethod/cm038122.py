def __init__(self, *, vllm_config: VllmConfig, prefix: str = ""):
        super().__init__(vllm_config=vllm_config, prefix=prefix)

        config = vllm_config.model_config.hf_config
        head_dtype = vllm_config.model_config.head_dtype

        hidden_size = getattr(config, "hidden_size", None)
        if hidden_size is None and hasattr(config, "text_config"):
            hidden_size = config.text_config.hidden_size
        if hidden_size is None:
            raise ValueError(
                "Unable to determine text hidden size from config. "
                "Expected 'hidden_size' or 'text_config.hidden_size'."
            )

        # (ColPali: dim, projection_dim, colbert_dim)
        self.embed_dim: int = (
            getattr(config, "embed_dim", None)
            or getattr(config, "dims", None)
            or getattr(config, "dim", None)
            or getattr(config, "projection_dim", None)
            or getattr(config, "colbert_dim", None)
            or 128  # default from reference implementation
        )

        self.custom_text_proj = nn.Linear(
            hidden_size,
            self.embed_dim,
            bias=False,
            dtype=head_dtype,
        )

        pooler_config = vllm_config.model_config.pooler_config
        assert pooler_config is not None
        self.pooler = pooler_for_token_embed(
            pooler_config,
            projector=None,
        )