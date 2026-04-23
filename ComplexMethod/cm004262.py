def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, SEWPositionalConvEmbedding):
            init.normal_(
                module.conv.weight,
                mean=0,
                std=2 * math.sqrt(1 / (module.conv.kernel_size[0] * module.conv.in_channels)),
            )
            init.constant_(module.conv.bias, 0)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, nn.Conv1d):
            if is_deepspeed_zero3_enabled():
                import deepspeed

                if hasattr(module, "weight_v") and hasattr(module, "weight_g"):
                    with deepspeed.zero.GatheredParameters([module.weight_v, module.weight_g], modifier_rank=0):
                        init.kaiming_normal_(module.weight)
                else:
                    with deepspeed.zero.GatheredParameters(module.weight, modifier_rank=0):
                        init.kaiming_normal_(module.weight)
            else:
                init.kaiming_normal_(module.weight)

        if isinstance(module, (nn.Linear, nn.Conv1d)) and module.bias is not None:
            init.zeros_(module.bias)