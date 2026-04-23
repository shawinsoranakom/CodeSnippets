def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, (nn.LayerNorm, nn.GroupNorm, nn.BatchNorm1d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
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

            if module.bias is not None:
                init.zeros_(module.bias)
        elif isinstance(module, HubertModel):
            if hasattr(module, "masked_spec_embed"):
                init.uniform_(module.masked_spec_embed)
        elif isinstance(module, HubertForSequenceClassification):
            if hasattr(module, "layer_weights"):
                init.constant_(module.layer_weights, 1.0 / (self.config.num_hidden_layers + 1))