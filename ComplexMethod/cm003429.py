def _init_weights(self, module):
        """Initialize the weights"""
        factor = self.config.initializer_factor  # Used for testing weights initialization
        if isinstance(module, Pix2StructLayerNorm):
            init.constant_(module.weight, factor * 1.0)
        elif isinstance(module, Pix2StructTextDenseGatedActDense):
            hidden_size = (
                self.config.text_config.hidden_size
                if isinstance(self.config, Pix2StructConfig)
                else self.config.hidden_size
            )
            d_ff = self.config.text_config.d_ff if isinstance(self.config, Pix2StructConfig) else self.config.d_ff

            init.normal_(module.wi_0.weight, mean=0.0, std=factor * ((hidden_size) ** -0.5))
            if hasattr(module.wi_0, "bias") and module.wi_0.bias is not None:
                init.zeros_(module.wi_0.bias)
            init.normal_(module.wi_1.weight, mean=0.0, std=factor * ((hidden_size) ** -0.5))
            if hasattr(module.wi_1, "bias") and module.wi_1.bias is not None:
                init.zeros_(module.wi_1.bias)
            init.normal_(module.wo.weight, mean=0.0, std=factor * ((d_ff) ** -0.5))
            if hasattr(module.wo, "bias") and module.wo.bias is not None:
                init.zeros_(module.wo.bias)
        elif isinstance(module, Pix2StructTextAttention):
            hidden_size = (
                self.config.text_config.hidden_size
                if isinstance(self.config, Pix2StructConfig)
                else self.config.hidden_size
            )
            key_value_proj_dim = (
                self.config.text_config.d_kv if isinstance(self.config, Pix2StructConfig) else self.config.hidden_size
            )
            n_heads = (
                self.config.text_config.num_heads
                if isinstance(self.config, Pix2StructConfig)
                else self.config.num_heads
            )

            init.normal_(module.query.weight, mean=0.0, std=factor * ((hidden_size * key_value_proj_dim) ** -0.5))
            init.normal_(module.key.weight, mean=0.0, std=factor * (hidden_size**-0.5))
            init.normal_(module.value.weight, mean=0.0, std=factor * (hidden_size**-0.5))
            init.normal_(module.output.weight, mean=0.0, std=factor * ((n_heads * key_value_proj_dim) ** -0.5))
            if module.has_relative_attention_bias:
                init.normal_(module.relative_attention_bias.weight, mean=0.0, std=factor * ((hidden_size) ** -0.5))
        elif isinstance(module, nn.Embedding):
            hidden_size = (
                self.config.text_config.hidden_size
                if isinstance(self.config, Pix2StructConfig)
                else self.config.hidden_size
            )

            init.normal_(module.weight, mean=0.0, std=factor * ((hidden_size) ** -0.5))
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, Pix2StructTextModel):
            hidden_size = (
                self.config.text_config.hidden_size
                if isinstance(self.config, Pix2StructConfig)
                else self.config.hidden_size
            )

            init.normal_(module.lm_head.weight, mean=0.0, std=factor * ((hidden_size) ** -0.5))
        elif isinstance(module, (nn.Linear, nn.Conv2d)):
            init.trunc_normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, Pix2StructLayerNorm):
            if module.weight is not None:
                init.ones_(module.weight)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])