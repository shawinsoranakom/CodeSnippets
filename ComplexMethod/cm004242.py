def _init_weights(self, module):
        """Initialize the weights"""
        factor = self.config.initializer_factor  # Used for testing weights initialization
        if isinstance(module, SwitchTransformersLayerNorm):
            init.constant_(module.weight, factor * 1.0)
        elif isinstance(
            module,
            (SwitchTransformersModel, SwitchTransformersForConditionalGeneration, SwitchTransformersEncoderModel),
        ):
            init.normal_(module.shared.weight, mean=0.0, std=factor * 1.0)
            if hasattr(module, "lm_head") and not self.config.tie_word_embeddings:
                init.normal_(module.lm_head.weight, mean=0.0, std=factor * 1.0)
        elif isinstance(module, SwitchTransformersDenseActDense):
            init.normal_(module.wi.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi, "bias") and module.wi.bias is not None:
                init.zeros_(module.wi.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((self.config.d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, SwitchTransformersAttention):
            d_model = self.config.d_model
            key_value_proj_dim = self.config.d_kv
            n_heads = self.config.num_heads
            init.normal_(module.q.weight, mean=0.0, std=factor * ((d_model * key_value_proj_dim) ** -0.5))
            init.normal_(module.k.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.v.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.o.weight, mean=0.0, std=factor * ((n_heads * key_value_proj_dim) ** -0.5))
            if module.has_relative_attention_bias:
                init.normal_(module.relative_attention_bias.weight, mean=0.0, std=factor * ((d_model) ** -0.5))
        elif isinstance(module, SwitchTransformersSparseMLP):
            d_model = self.config.d_model
            key_value_proj_dim = self.config.d_kv
            n_heads = self.config.num_heads
            init.normal_(module.router.classifier.weight, mean=0.0, std=factor * 1)
            for idx in range(self.config.num_experts):
                init.normal_(module.experts[f"expert_{idx}"].wi.weight, mean=0.0, std=factor * (d_model**-0.5))
                init.normal_(module.experts[f"expert_{idx}"].wo.weight, mean=0.0, std=factor * (d_model**-0.5))