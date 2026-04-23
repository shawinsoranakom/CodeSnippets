def forward(
        self,
        src: list[torch.Tensor],
        prompt: torch.Tensor,
        src_key_padding_mask: list[torch.Tensor] | None = None,
        src_pos: list[torch.Tensor] | None = None,
        prompt_key_padding_mask: torch.Tensor = None,
        feat_sizes: list[int] | None = None,
        encoder_extra_kwargs: dict | None = None,
    ):
        """Forward pass for the transformer encoder with text-image fusion."""
        # Restore spatial shapes of vision
        bs = src[0].shape[1]  # seq first
        if feat_sizes is not None:
            assert len(feat_sizes) == len(src)
            if src_key_padding_mask is None:
                src_key_padding_mask = [None] * len(src)
            for i, (h, w) in enumerate(feat_sizes):
                src[i] = src[i].reshape(h, w, bs, -1).permute(2, 3, 0, 1)
                src_pos[i] = src_pos[i].reshape(h, w, bs, -1).permute(2, 3, 0, 1)
                src_key_padding_mask[i] = (
                    src_key_padding_mask[i].reshape(h, w, bs).permute(2, 0, 1)
                    if src_key_padding_mask[i] is not None
                    else None
                )
        else:
            assert all(x.dim == 4 for x in src), "expected list of (bs, c, h, w) tensors"

        if self.add_pooled_text_to_img_feat:
            # Fusion: Add mean pooled text to image features
            pooled_text = pool_text_feat(prompt, prompt_key_padding_mask, self.pool_text_with_mask)
            pooled_text = self.text_pooling_proj(pooled_text)[..., None, None]  # prompt is seq first
            src = [x.add_(pooled_text) for x in src]

        (
            out,
            key_padding_masks_flatten,
            lvl_pos_embed_flatten,
            level_start_index,
            spatial_shapes,
            valid_ratios,
        ) = super().forward(
            src,
            src_key_padding_masks=src_key_padding_mask,
            pos=src_pos,
            prompt=prompt.transpose(0, 1),
            prompt_key_padding_mask=prompt_key_padding_mask,
            encoder_extra_kwargs=encoder_extra_kwargs,
        )

        return {
            "memory": out,
            "padding_mask": key_padding_masks_flatten,
            "pos_embed": lvl_pos_embed_flatten,
            "memory_text": prompt,
            "level_start_index": level_start_index,
            "spatial_shapes": spatial_shapes,
            "valid_ratios": valid_ratios,
        }