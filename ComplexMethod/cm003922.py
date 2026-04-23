def _init_weights(self, module):
        """Initialize the weights"""
        if hasattr(self.config, "initializer_factor"):
            init_factor = self.config.initializer_factor
            init_range = self.config.initializer_range
            std = init_range * init_factor
        elif hasattr(self.config, "vision_config"):
            init_factor = self.config.vision_config.initializer_factor
            init_range = self.config.vision_config.initializer_range
            std = init_range * init_factor

        if hasattr(self.config, "init_std"):
            std = self.config.init_std
        elif hasattr(self.config, "text_config"):
            std = self.config.text_config.init_std

        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, (nn.LayerNorm, Kosmos2_5LayerNorm)):
            init.ones_(module.weight)
            if getattr(module, "bias", None) is not None:
                init.zeros_(module.bias)
        elif isinstance(module, Kosmos2_5ImageToTextProjection):
            init.normal_(module.latent_query, mean=0.0, std=1.0)
        elif isinstance(module, Kosmos2_5TextSinusoidalPositionalEmbedding):
            emb_weights = module.get_embedding(
                module.num_positions + module.offset, module.embedding_dim, module.padding_idx
            )
            init.copy_(module.weights, emb_weights)