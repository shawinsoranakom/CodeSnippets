def _init_weights(self, module: nn.Module):
        """
        Initialize weights
        """
        if isinstance(module, PatchTSTPositionalEncoding):
            # get the number of patches
            num_patches = (
                max(self.config.context_length, self.config.patch_length) - self.config.patch_length
            ) // self.config.patch_stride + 1
            # initialize cls_token
            if self.config.use_cls_token:
                init.normal_(module.cls_token, std=0.02)
                num_patches += 1
            # initialize positional encoding
            position_enc = module._init_pe(self.config, num_patches)
            if is_deepspeed_zero3_enabled():
                import deepspeed

                with deepspeed.zero.GatheredParameters(module.position_enc, modifier_rank=None):
                    if module.position_enc.numel() > 0:
                        init.copy_(module.position_enc, position_enc)
            else:
                init.copy_(module.position_enc, position_enc)
        elif isinstance(module, (nn.LayerNorm, nn.BatchNorm1d)):
            init.zeros_(module.bias)
            init.ones_(module.weight)
            if getattr(module, "running_mean", None) is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)
        elif isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.init_std)
            if module.bias is not None:
                init.zeros_(module.bias)