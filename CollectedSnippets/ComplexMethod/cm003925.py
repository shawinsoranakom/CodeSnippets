def _init_weights(self, module: nn.Linear | nn.Conv2d | nn.LayerNorm) -> None:
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Conv2d)):
            init.trunc_normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, VitDetEmbeddings):
            init.trunc_normal_(module.position_embeddings, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, VitDetAttention) and self.config.use_relative_position_embeddings:
            init.trunc_normal_(module.rel_pos_h, mean=0.0, std=self.config.initializer_range)
            init.trunc_normal_(module.rel_pos_w, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, VitDetResBottleneckBlock):
            for layer in [module.conv1, module.conv2, module.conv3]:
                init.kaiming_normal_(layer.weight, mode="fan_out", nonlinearity="relu")
                if layer.bias is not None:
                    init.constant_(layer.bias, 0)
            for layer in [module.norm1, module.norm2]:
                init.ones_(layer.weight)
                init.zeros_(layer.bias)
            # zero init last norm layer.
            init.zeros_(module.norm3.weight)
            init.zeros_(module.norm3.bias)