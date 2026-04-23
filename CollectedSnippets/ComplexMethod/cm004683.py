def _init_weights(self, module):
        """Initialize the weights"""
        factor = self.config.initializer_factor  # Used for testing weights initialization
        if isinstance(module, Pop2PianoLayerNorm):
            init.constant_(module.weight, factor * 1.0)
        elif isinstance(module, Pop2PianoConcatEmbeddingToMel):
            init.normal_(module.embedding.weight, mean=0.0, std=factor * 1.0)
        elif isinstance(module, Pop2PianoForConditionalGeneration):
            init.normal_(module.shared.weight, mean=0.0, std=factor * 1.0)
            if hasattr(module, "lm_head"):
                init.normal_(module.lm_head.weight, mean=0.0, std=factor * 1.0)
        elif isinstance(module, Pop2PianoDenseActDense):
            init.normal_(module.wi.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi, "bias") and module.wi.bias is not None:
                init.zeros_(module.wi.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((self.config.d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, Pop2PianoDenseGatedActDense):
            init.normal_(module.wi_0.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi_0, "bias") and module.wi_0.bias is not None:
                init.zeros_(module.wi_0.bias)
            init.normal_(module.wi_1.weight, mean=0.0, std=factor * ((self.config.d_model) ** -0.5))
            if hasattr(module.wi_1, "bias") and module.wi_1.bias is not None:
                init.zeros_(module.wi_1.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((self.config.d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, Pop2PianoAttention):
            d_model = self.config.d_model
            key_value_proj_dim = self.config.d_kv
            n_heads = self.config.num_heads
            init.normal_(module.q.weight, mean=0.0, std=factor * ((d_model * key_value_proj_dim) ** -0.5))
            init.normal_(module.k.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.v.weight, mean=0.0, std=factor * (d_model**-0.5))
            init.normal_(module.o.weight, mean=0.0, std=factor * ((n_heads * key_value_proj_dim) ** -0.5))
            if module.has_relative_attention_bias:
                init.normal_(module.relative_attention_bias.weight, mean=0.0, std=factor * ((d_model) ** -0.5))