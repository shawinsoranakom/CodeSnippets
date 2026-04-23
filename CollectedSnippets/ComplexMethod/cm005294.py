def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif hasattr(module, "latents"):
            init.normal_(module.latents, mean=0.0, std=self.config.initializer_range)
        elif hasattr(module, "position_embeddings") and isinstance(module, PerceiverTrainablePositionEncoding):
            init.normal_(module.position_embeddings, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.ParameterDict):
            for modality in module:
                init.normal_(module[modality], mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)