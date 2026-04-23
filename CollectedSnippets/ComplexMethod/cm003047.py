def _init_weights(self, module):
        """Initialize weights"""
        if isinstance(module, PatchTSMixerPositionalEncoding):
            # initialize positional encoding
            if self.config.positional_encoding_type == "random":
                init.normal_(module.position_enc, mean=0.0, std=0.1)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm1d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, PatchTSMixerBatchNorm):
            init.zeros_(module.batchnorm.bias)
            init.ones_(module.batchnorm.weight)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.init_std)
            if module.bias is not None:
                init.zeros_(module.bias)