def _init_weights(self, module):
        PreTrainedModel._init_weights(self, module)
        if isinstance(module, Gemma3nAudioCumulativeGroupNorm):
            init.ones_(module.weight)
        elif isinstance(module, Gemma3nAudioAttention):
            init.zeros_(module.per_dim_scale)
            q_scale = module.head_dim**-0.5
            r_softplus_0 = 1.0 / torch.nn.functional.softplus(torch.tensor(0.0))
            init.copy_(module.q_scale, q_scale * r_softplus_0)
            init.constant_(module.softcap, module.attention_logits_soft_cap)
            init.copy_(module.local_causal_valid_mask, module.create_local_causal_valid_mask())
        elif isinstance(module, Gemma3nTextScaledWordEmbedding):
            init.constant_(module.embed_scale, module.scalar_embed_scale)
        elif isinstance(module, Gemma3nTextAltUp):
            init.zeros_(module.correct_output_scale)
            init.constant_(module.router_input_scale, self.config.hidden_size**-1.0)
        elif isinstance(module, Gemma3nAudioRelativePositionEmbedding):
            min_timescale, max_timescale = 1.0, 1.0e4
            num_timescales = module.channels // 2
            log_timescale_increment = math.log(float(max_timescale) / float(min_timescale)) / max(
                num_timescales - 1, 1
            )
            inv_timescales = min_timescale * torch.exp(torch.arange(num_timescales) * -log_timescale_increment)
            init.copy_(module.inv_timescales, inv_timescales.float().unsqueeze(0).unsqueeze(0))
        elif isinstance(module, Gemma3nTextModel):
            init.constant_(module.per_layer_projection_scale, self.hidden_size**-0.5)
            init.constant_(module.per_layer_input_scale, 1 / math.sqrt(2.0))
        elif isinstance(module, Gemma3nRotaryEmbedding):
            for layer_type in module.layer_types:
                rope_init_fn = module.compute_default_rope_parameters
                if module.rope_type[layer_type] != "default":
                    rope_init_fn = ROPE_INIT_FUNCTIONS[module.rope_type[layer_type]]
                curr_inv_freq, _ = rope_init_fn(module.config, layer_type=layer_type)
                init.copy_(getattr(module, f"{layer_type}_inv_freq"), curr_inv_freq)
                init.copy_(getattr(module, f"{layer_type}_original_inv_freq"), curr_inv_freq)

        if hasattr(module, "gradient_clipping"):
            init.constant_(module.gradient_clipping, self.config.gradient_clipping)