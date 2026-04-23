def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        factor = self.config.initializer_factor

        if isinstance(module, ClapTextEmbeddings):
            init.normal_(module.position_embeddings.weight, mean=0.0, std=factor * 0.02)
            init.normal_(module.token_type_embeddings.weight, mean=0.0, std=factor * 0.02)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
            init.zeros_(module.token_type_ids)
        elif isinstance(module, ClapModel):
            init.constant_(module.logit_scale_a, math.log(self.config.logit_scale_init_value))
            init.constant_(module.logit_scale_t, math.log(self.config.logit_scale_init_value))
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=factor * 0.02)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, (nn.Conv2d, nn.Linear)):
            in_proj_std = (self.config.hidden_size**-0.5) * ((2 * self.config.num_hidden_layers) ** -0.5) * factor
            init.normal_(module.weight, std=in_proj_std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, ClapAudioSelfAttention):
            init.zeros_(module.relative_position_bias_table)
            init.copy_(module.relative_position_index, module.create_relative_position_index())