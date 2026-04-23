def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, (QuantLinear, nn.Linear)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
            if getattr(module, "weight_integer", None) is not None:
                init.zeros_(module.weight_integer)
                init.zeros_(module.fc_scaling_factor)
            if getattr(module, "bias_integer", None) is not None:
                init.zeros_(module.bias_integer)
        elif isinstance(module, (QuantEmbedding, nn.Embedding)):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
            if getattr(module, "weight_scaling_factor", None) is not None:
                init.zeros_(module.weight_scaling_factor)
                init.zeros_(module.weight_integer)
        elif isinstance(module, (IntLayerNorm, nn.LayerNorm)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "shift", None) is not None:
                init.zeros_(module.shift)
        elif isinstance(module, IBertLMHead):
            init.zeros_(module.bias)
        elif isinstance(module, IBertEmbeddings):
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, QuantAct):
            init.constant_(module.x_min, -1e-5)
            init.constant_(module.x_max, 1e-5)
            init.zeros_(module.act_scaling_factor)