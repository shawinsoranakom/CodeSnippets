def _init_weights(self, module):
        if isinstance(module, (nn.Conv2d, nn.Conv3d)):
            init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            if module.bias is not None:
                fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(module.weight)
                bound = 1 / math.sqrt(fan_in)
                init.uniform_(module.bias, -bound, bound)
        elif isinstance(module, nn.Linear):
            init.kaiming_uniform_(module.weight, a=math.sqrt(5))
            if module.bias is not None:
                fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(module.weight)
                bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
                init.uniform_(module.bias, -bound, bound)
        elif isinstance(module, (nn.BatchNorm2d, nn.BatchNorm3d, nn.GroupNorm)):
            init.constant_(module.weight, 1.0)
            init.constant_(module.bias, 0.0)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])