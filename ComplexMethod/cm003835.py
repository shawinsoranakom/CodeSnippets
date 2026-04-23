def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        std = self.config.initializer_range
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, AlignModel):
            init.xavier_uniform_(module.text_projection.weight)
            init.zeros_(module.text_projection.bias)
            init.constant_(module.temperature, self.config.temperature_init_value)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        if isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, AlignTextEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
            init.zeros_(module.token_type_ids)