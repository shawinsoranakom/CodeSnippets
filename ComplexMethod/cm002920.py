def _init_weights(self, module: nn.Module) -> None:
        std = self.config.initializer_range
        if isinstance(module, (nn.Linear, nn.Conv2d, nn.ConvTranspose2d)):
            init.kaiming_uniform_(module.weight, a=math.sqrt(5))
            if module.bias is not None:
                fan_in, _ = torch.nn.init._calculate_fan_in_and_fan_out(module.weight)
                bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
                init.uniform_(module.bias, -bound, bound)
        elif isinstance(module, nn.LayerNorm):
            init.ones_(module.weight)
            init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=1)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, EomtLayerScale):
            if hasattr(module, "lambda1"):
                init.constant_(module.lambda1, self.config.layerscale_value)
        elif isinstance(module, EomtEmbeddings):
            init.trunc_normal_(module.cls_token, mean=0.0, std=std)
            init.zeros_(module.register_tokens)
            init.copy_(module.position_ids, torch.arange(module.position_ids.shape[-1]).expand((1, -1)))
        elif isinstance(module, EomtLoss):
            empty_weight = torch.ones(module.num_labels + 1)
            empty_weight[-1] = module.eos_coef
            init.copy_(module.empty_weight, empty_weight)
        elif isinstance(module, EomtForUniversalSegmentation):
            init.ones_(module.attn_mask_probs)