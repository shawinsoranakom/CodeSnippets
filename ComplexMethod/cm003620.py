def _init_weights(self, module):
        """
        Initialize weights function to properly initialize Linear layer weights.
        Since model architectures may vary, we assume only the classifier requires
        initialization, while all other weights should be loaded from the checkpoint.
        """
        if isinstance(module, nn.Linear):
            init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                init.zeros_(module.bias)
        # Also, reinit all non-persistent buffers if any!
        if hasattr(module, "init_non_persistent_buffers"):
            module.init_non_persistent_buffers()
        elif (
            hasattr(module, "_get_pos_embed_values")
            and hasattr(module, "feat_shape")
            and module.feat_shape is not None
        ):
            module.pos_embed = module._get_pos_embed_values(
                feat_shape=module.feat_shape,
                device=module.pos_embed.device if module.pos_embed is not None else None,
                dtype=module.pos_embed.dtype if module.pos_embed is not None else torch.float32,
            )
        elif isinstance(module, nn.BatchNorm2d):
            # TimmWrapper always creates models with pretrained=False, so buffers are never pre-loaded
            # Always initialize buffers (handles both meta device and to_empty() cases)
            running_mean = getattr(module, "running_mean", None)
            if running_mean is not None:
                init.zeros_(module.running_mean)
                init.ones_(module.running_var)
                init.zeros_(module.num_batches_tracked)