def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        factor = self.config.initializer_factor
        if isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=factor * 0.02)
        elif isinstance(module, (nn.Linear, Conv1D, nn.Conv1d)):
            init.normal_(module.weight, mean=0.0, std=factor * 0.02)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, ClvpRMSNorm):
            init.ones_(module.weight)
        elif isinstance(module, ClvpEncoderMLP):
            in_proj_std = (module.config.hidden_size**-0.5) * ((2 * module.config.num_hidden_layers) ** -0.5) * factor
            fc_std = (2 * module.config.hidden_size) ** -0.5 * factor
            init.normal_(module.fc1.proj.weight if getattr(module.fc1, "proj") else module.fc1.weight, std=fc_std)
            init.normal_(module.fc2.weight, std=in_proj_std)
        elif isinstance(module, ClvpEncoder):
            config = self.config.get_text_config()
            factor = config.initializer_factor
            init.normal_(module.projection.weight, mean=0.0, std=factor * (config.hidden_size**-0.5))
        elif isinstance(module, ClvpConditioningEncoder):
            init.normal_(module.mel_conv.weight, mean=0.0, std=factor)
            init.zeros_(module.mel_conv.bias)
        elif isinstance(module, ClvpForCausalLM):
            for name, p in module.named_parameters():
                if name == "c_proj.weight":
                    init.normal_(
                        p, mean=0.0, std=self.config.initializer_range / math.sqrt(2 * self.config.num_hidden_layers)
                    )
        elif isinstance(module, ClvpModelForConditionalGeneration):
            init.constant_(module.logit_scale, self.config.logit_scale_init_value)
        elif isinstance(module, ClvpSelfAttention):
            if hasattr(module.config, "max_position_embeddings"):
                max_positions = module.config.max_position_embeddings
                bias = torch.tril(torch.ones((max_positions, max_positions), dtype=torch.bool))
                bias = bias.view(1, 1, max_positions, max_positions)
                init.copy_(module.bias, bias)
        elif isinstance(module, ClvpRotaryPositionalEmbedding):
            dim = max(self.config.projection_dim // (self.config.num_attention_heads * 2), 32)
            inv_freq = 1.0 / (10000 ** (torch.arange(0, dim, 2, dtype=torch.int64).float() / dim))
            init.copy_(module.inv_freq, inv_freq)
        if isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.zeros_(module.bias)
            init.ones_(module.weight)