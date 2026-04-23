def _init_weights(self, module) -> None:
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.trunc_normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, DINOv3ViTEmbeddings):
            init.trunc_normal_(module.cls_token, mean=0.0, std=self.config.initializer_range)
            if module.config.num_register_tokens > 0:
                init.trunc_normal_(module.register_tokens, mean=0.0, std=self.config.initializer_range)
            init.zeros_(module.mask_token)
        elif isinstance(module, DINOv3ViTLayerScale):
            init.constant_(module.lambda1, self.config.layerscale_value)
        elif isinstance(module, DINOv3ViTRopePositionEmbedding):
            inv_freq = 1 / module.base ** torch.arange(0, 1, 4 / module.head_dim, dtype=torch.float32)
            init.copy_(module.inv_freq, inv_freq)