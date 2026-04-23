def _init_weights(self, module: nn.Module) -> None:
        """Initialize the weights"""
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            init.trunc_normal_(module.weight, std=0.02)
            if module.bias is not None:
                init.constant_(module.bias, 0)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm2d)):
            init.constant_(module.bias, 0)
            init.constant_(module.weight, 1.0)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, (SwiftFormerConvEncoder, SwiftFormerLocalRepresentation)):
            init.ones_(module.layer_scale)
        elif isinstance(module, SwiftFormerEncoderBlock):
            if self.config.use_layer_scale:
                init.constant_(module.layer_scale_1, self.config.layer_scale_init_value)
                init.constant_(module.layer_scale_2, self.config.layer_scale_init_value)
        elif isinstance(module, SwiftFormerEfficientAdditiveAttention):
            init.normal_(module.w_g)