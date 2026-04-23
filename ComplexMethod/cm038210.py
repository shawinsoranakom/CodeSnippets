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
        self._proj_hidden_size = hidden_size

        # ColPali uses embedding_dim=128, but also check other naming variants
        self.embed_dim: int | None = (
            getattr(config, "embedding_dim", None)
            or getattr(config, "embed_dim", None)
            or getattr(config, "dim", None)
            or getattr(config, "projection_dim", None)
            or getattr(config, "colbert_dim", None)
        )

        # Build the projection layer if embed_dim is known
        if self.embed_dim is not None:
            self.custom_text_proj = nn.Linear(
                hidden_size,
                self.embed_dim,
                bias=False,
                dtype=head_dtype,
            )
        else:
            # Will be created during load_weights when dim is inferred
            self.custom_text_proj = None

        pooler_config = vllm_config.model_config.pooler_config
        assert pooler_config is not None
        self.pooler = pooler_for_token_embed(
            pooler_config,
            projector=self.custom_text_proj,
        )