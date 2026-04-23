def _init_weights(self, module):
        PreTrainedModel._init_weights(self, module)
        if isinstance(module, T5Gemma2MultiModalProjector):
            init.zeros_(module.mm_input_projection_weight)
        elif isinstance(module, T5Gemma2TextScaledWordEmbedding):
            init.zeros_(module.eoi_embedding)
            init.constant_(module.embed_scale, module.scalar_embed_scale)
        elif isinstance(module, T5Gemma2ClassificationHead):
            scale = module.out_proj.weight.shape[0] ** -0.5
            init.normal_(module.out_proj.weight, mean=0.0, std=self.config.initializer_range * scale)
            if hasattr(module.out_proj, "bias") and module.out_proj.bias is not None:
                init.zeros_(module.out_proj.bias)
        # We initialize with 0s to be 1 centered as the RMSNorm here does (1 + weight)
        elif "RMSNorm" in module.__class__.__name__:
            init.zeros_(module.weight)
        elif isinstance(module, T5Gemma2RotaryEmbedding):
            for layer_type in module.layer_types:
                rope_init_fn = module.compute_default_rope_parameters
                if module.rope_type[layer_type] != "default":
                    rope_init_fn = ROPE_INIT_FUNCTIONS[module.rope_type[layer_type]]
                curr_inv_freq, _ = rope_init_fn(module.config, layer_type=layer_type)
                init.copy_(getattr(module, f"{layer_type}_inv_freq"), curr_inv_freq)
                init.copy_(getattr(module, f"{layer_type}_original_inv_freq"), curr_inv_freq)