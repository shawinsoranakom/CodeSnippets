def _init_weights(self, module: nn.Module):
        """Initialize the weights"""
        if isinstance(module, (nn.Linear, nn.Embedding)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, nn.Conv2d):
            init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            if module.bias is not None:
                init.constant_(module.bias, 0)
        elif isinstance(module, TvpModel):
            init.normal_(module.text_prompt)

        if isinstance(module, nn.Linear) and module.bias is not None:
            init.zeros_(module.bias)
        if hasattr(module, "pad_up"):
            init.normal_(module.pad_up)
        if hasattr(module, "pad_down"):
            init.normal_(module.pad_down)
        if hasattr(module, "pad_left"):
            init.normal_(module.pad_left)
        if hasattr(module, "pad_right"):
            init.normal_(module.pad_right)