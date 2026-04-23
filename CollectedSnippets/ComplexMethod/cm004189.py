def _init_weights(self, module: nn.Module):
        xavier_std = self.config.init_xavier_std
        std = self.config.init_std
        if isinstance(module, MaskFormerTransformerModule):
            if module.input_projection is not None:
                init.xavier_uniform_(module.input_projection.weight, gain=xavier_std)
                init.constant_(module.input_projection.bias, 0)
        # FPN
        elif isinstance(module, MaskFormerFPNModel):
            init.xavier_uniform_(module.stem.get_submodule("0").weight, gain=xavier_std)

        elif isinstance(module, MaskFormerFPNLayer):
            init.xavier_uniform_(module.proj[0].weight, gain=xavier_std)

        elif isinstance(module, MaskFormerFPNConvLayer):
            init.xavier_uniform_(module.get_submodule("0").weight, gain=xavier_std)
        # The MLP head
        elif isinstance(module, MaskformerMLPPredictionHead):
            # I was not able to find the correct initializer in the original implementation
            # we'll use xavier
            for submodule in module.modules():
                if isinstance(submodule, nn.Linear):
                    init.xavier_uniform_(submodule.weight, gain=xavier_std)
                    init.constant_(submodule.bias, 0)
        elif isinstance(module, nn.LayerNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        # copied from DETR
        if isinstance(module, (nn.Linear, nn.Conv2d, nn.BatchNorm2d)):
            init.normal_(module.weight, mean=0.0, std=std)
            if module.bias is not None:
                init.zeros_(module.bias)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, nn.Embedding):
            init.normal_(module.weight, mean=0.0, std=std)
            # Here we need the check explicitly, as we slice the weight in the `zeros_` call, so it looses the flag
            if module.padding_idx is not None and not getattr(module.weight, "_is_hf_initialized", False):
                init.zeros_(module.weight[module.padding_idx])
        elif isinstance(module, MaskFormerLoss):
            empty_weight = torch.ones(module.num_labels + 1)
            empty_weight[-1] = module.eos_coef
            init.copy_(module.empty_weight, empty_weight)