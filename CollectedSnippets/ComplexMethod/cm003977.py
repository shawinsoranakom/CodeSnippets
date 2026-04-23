def _init_weights(self, module):
        super()._init_weights(module)
        if isinstance(module, Gemma4VisionPatchEmbedder):
            init.ones_(module.position_embedding_table)
        elif isinstance(module, Gemma4AudioRelPositionalEncoding):
            min_timescale = 1.0
            max_timescale = 10000.0
            num_timescales = module.hidden_size // 2
            log_timescale_increment = math.log(max_timescale / min_timescale) / max(num_timescales - 1, 1)
            inv_timescales = min_timescale * torch.exp(torch.arange(num_timescales) * -log_timescale_increment)
            init.copy_(module.inv_timescales, inv_timescales.unsqueeze(0).unsqueeze(0))
        elif isinstance(module, Gemma4AudioAttention):
            init.constant_(module.softcap, module.attention_logits_soft_cap)
            init.zeros_(module.per_dim_scale)
        elif isinstance(module, Gemma4TextRotaryEmbedding):
            for layer_type, rope_init_fn in module.rope_init_fns.items():
                rope_init_fn_kwargs = {"layer_type": layer_type}
                if layer_type == "full_attention" and module.rope_type[layer_type] == "proportional":
                    rope_init_fn_kwargs["head_dim_key"] = "global_head_dim"

                curr_inv_freq, _ = rope_init_fn(module.config, **rope_init_fn_kwargs)
                init.copy_(getattr(module, f"{layer_type}_inv_freq"), curr_inv_freq)
                init.copy_(getattr(module, f"{layer_type}_original_inv_freq"), curr_inv_freq)
        elif isinstance(module, Gemma4VisionRotaryEmbedding):
            rope_fn = (
                ROPE_INIT_FUNCTIONS[module.rope_type]
                if module.rope_type != "default"
                else module.compute_default_rope_parameters
            )
            buffer_value, _ = rope_fn(module.config)
            init.copy_(module.inv_freq, buffer_value)
            init.copy_(module.original_inv_freq, buffer_value)
        elif isinstance(module, Gemma4TextScaledWordEmbedding):
            init.constant_(module.embed_scale, module.scalar_embed_scale)
        elif isinstance(module, Gemma4TextRouter):
            init.ones_(module.scale)
            init.ones_(module.per_expert_scale)
        elif isinstance(module, Gemma4TextExperts):
            std = self.config.initializer_range
            init.normal_(module.gate_up_proj, mean=0.0, std=std)
            init.normal_(module.down_proj, mean=0.0, std=std)
        elif isinstance(module, Gemma4TextDecoderLayer):
            init.ones_(module.layer_scalar)
        elif isinstance(module, Gemma4ClippableLinear) and module.use_clipped_linears:
            init.constant_(module.input_min, -float("inf"))
            init.constant_(module.input_max, float("inf"))
            init.constant_(module.output_min, -float("inf"))
            init.constant_(module.output_max, float("inf"))
        elif isinstance(module, Gemma4VisionModel) and module.config.standardize:
            init.zeros_(module.std_bias)
            init.ones_(module.std_scale)