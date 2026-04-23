def _init_weights(self, module):
        """Initialize the weights."""
        if isinstance(module, nn.Embedding):
            if self.config is not None and self.config.embed_init_std is not None:
                init.normal_(module.weight, mean=0, std=self.config.embed_init_std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        if isinstance(module, nn.Linear):
            if self.config is not None and self.config.init_std is not None:
                init.normal_(module.weight, mean=0, std=self.config.init_std)
                if module.bias is not None:
                    init.constant_(module.bias, 0.0)
        if isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        if isinstance(module, XLMModel):
            if self.config.sinusoidal_embeddings:
                init.copy_(
                    module.position_embeddings.weight,
                    create_sinusoidal_embeddings(
                        self.config.max_position_embeddings,
                        self.config.emb_dim,
                        out=torch.empty_like(module.position_embeddings.weight),
                    ),
                )
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))