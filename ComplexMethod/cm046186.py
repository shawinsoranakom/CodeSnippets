def forward(
        self,
        src: list[torch.Tensor],
        src_key_padding_masks: list[torch.Tensor] | None = None,
        pos: list[torch.Tensor] | None = None,
        prompt: torch.Tensor = None,
        prompt_key_padding_mask: torch.Tensor = None,
        encoder_extra_kwargs: dict | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Process multi-level features through the transformer encoder.

        Args:
            src: List of multi-level features, each with shape (batch_size, channels, height, width)
            src_key_padding_masks: List of padding masks for each feature level, each with shape (batch_size, height,
                width)
            pos: List of positional embeddings for each feature level, each with shape (batch_size, channels, height,
                width)
            prompt: Optional text/prompt features to attend to, with shape (seq_len, batch_size, d_model)
            prompt_key_padding_mask: Optional padding mask for prompt, with shape (batch_size, seq_len)
            encoder_extra_kwargs: Optional additional arguments to pass to each encoder layer

        Returns:
            A tuple containing:
            - output: Processed features with shape (seq_len, batch_size, d_model)
            - key_padding_masks_flatten: Flattened padding masks
            - lvl_pos_embed_flatten: Flattened positional embeddings
            - level_start_index: Starting indices for each feature level
            - spatial_shapes: Spatial dimensions of each feature level
            - valid_ratios: Valid ratios for each feature level
        """
        assert len(src) == self.num_feature_levels, "must be equal to num_feature_levels"
        if src_key_padding_masks is not None:
            assert len(src_key_padding_masks) == self.num_feature_levels
        if pos is not None:
            assert len(pos) == self.num_feature_levels
        # Flatten multilevel feats and add level pos embeds
        (
            src_flatten,
            key_padding_masks_flatten,
            lvl_pos_embed_flatten,
            level_start_index,
            valid_ratios,
            spatial_shapes,
        ) = self._prepare_multilevel_features(src, src_key_padding_masks, pos)

        output = src_flatten
        for layer in self.layers:
            layer_kwargs = {}

            assert isinstance(layer, TransformerEncoderLayer)
            layer_kwargs["memory"] = prompt
            layer_kwargs["memory_key_padding_mask"] = prompt_key_padding_mask
            layer_kwargs["query_pos"] = lvl_pos_embed_flatten
            layer_kwargs["tgt"] = output
            layer_kwargs["tgt_key_padding_mask"] = key_padding_masks_flatten

            if self.training:
                assert self.use_act_checkpoint, "activation ckpt not enabled in encoder"
            if encoder_extra_kwargs is not None:
                layer_kwargs.update(encoder_extra_kwargs)
            output = layer(**layer_kwargs)
        # return as seq first
        return (
            output.transpose(0, 1),
            (key_padding_masks_flatten.transpose(0, 1) if key_padding_masks_flatten is not None else None),
            lvl_pos_embed_flatten.transpose(0, 1),
            level_start_index,
            spatial_shapes,
            valid_ratios,
        )