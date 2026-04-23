def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, GitVisionEmbeddings):
            init.normal_(module.class_embedding, mean=0.0, std=self.config.initializer_range)
            init.normal_(module.patch_embedding.weight, std=self.config.initializer_range)
            init.normal_(module.position_embedding.weight, std=self.config.initializer_range)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, GitEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))