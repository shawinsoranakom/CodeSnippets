def _init_weights(self, module: nn.Module):
        cutoff_factor = self.config.initializer_cutoff_factor
        if cutoff_factor is None:
            cutoff_factor = 3

        def init_weight(module: nn.Module, std: float):
            init.trunc_normal_(
                module.weight,
                mean=0.0,
                std=std,
                a=-cutoff_factor * std,
                b=cutoff_factor * std,
            )

            if isinstance(module, nn.Linear):
                if module.bias is not None:
                    init.zeros_(module.bias)

        stds = {
            "in": self.config.initializer_range,
            "out": self.config.initializer_range / math.sqrt(2.0 * self.config.num_hidden_layers),
            "embedding": self.config.initializer_range,
            "final_out": self.config.hidden_size**-0.5,
        }

        if isinstance(module, ModernBertDecoderEmbeddings):
            init_weight(module.tok_embeddings, stds["embedding"])
        elif isinstance(module, ModernBertDecoderMLP):
            init_weight(module.Wi, stds["in"])
            init_weight(module.Wo, stds["out"])
        elif isinstance(module, ModernBertDecoderAttention):
            init_weight(module.q_proj, stds["in"])
            init_weight(module.k_proj, stds["in"])
            init_weight(module.v_proj, stds["in"])
            init_weight(module.Wo, stds["out"])
        elif isinstance(module, ModernBertDecoderPredictionHead):
            init_weight(module.dense, stds["out"])
        elif isinstance(module, ModernBertDecoderForSequenceClassification):
            init_weight(module.classifier, stds["final_out"])
        elif isinstance(module, ModernBertDecoderForCausalLM):
            init_weight(module.decoder, stds["out"])
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, ModernBertDecoderRotaryEmbedding):
            for layer_type in module.layer_types:
                rope_init_fn = module.compute_default_rope_parameters
                if module.rope_type[layer_type] != "default":
                    rope_init_fn = ROPE_INIT_FUNCTIONS[module.rope_type[layer_type]]
                curr_inv_freq, _ = rope_init_fn(module.config, layer_type=layer_type)
                init.copy_(getattr(module, f"{layer_type}_inv_freq"), curr_inv_freq)
                init.copy_(getattr(module, f"{layer_type}_original_inv_freq"), curr_inv_freq)