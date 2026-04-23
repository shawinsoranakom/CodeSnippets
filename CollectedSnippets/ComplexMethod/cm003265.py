def _init_weights(self, module):
        std = getattr(self.config, "initializer_range", self.config.get_text_config().initializer_range)

        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, MllamaTextRMSNorm):
            init.ones_(module.weight)
        elif isinstance(module, MllamaVisionModel):
            init.normal_(module.class_embedding, std=std)
        elif isinstance(module, MllamaPrecomputedPositionEmbedding):
            init.normal_(module.embedding, std=std)
            init.zeros_(module.gate)
        elif isinstance(module, MllamaVisionEncoderLayer) and module.is_gated:
            init.normal_(module.gate_attn, std=std)
            init.normal_(module.gate_ffn, std=std)
        elif isinstance(module, MllamaCrossAttentionDecoderLayer):
            init.zeros_(module.cross_attn_attn_gate)
            init.zeros_(module.cross_attn_mlp_gate)
        elif isinstance(module, MllamaPrecomputedAspectRatioEmbedding):
            if module.is_gated:
                init.zeros_(module.gate)
        elif isinstance(module, MllamaRotaryEmbedding):
            rope_fn = (
                ROPE_INIT_FUNCTIONS[module.rope_type]
                if module.rope_type != "default"
                else module.compute_default_rope_parameters
            )
            buffer_value, _ = rope_fn(module.config)
            init.copy_(module.inv_freq, buffer_value)
            init.copy_(module.original_inv_freq, buffer_value)