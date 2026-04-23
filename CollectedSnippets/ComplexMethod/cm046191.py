def forward(self, geo_prompt: Prompt, img_feats, img_sizes, img_pos_embeds=None):
        """Encode geometric box prompts.

        Args:
            geo_prompt (Prompt): Prompt object containing box embeddings, masks, and labels.
            img_feats (list[torch.Tensor]): List of image features from backbone.
            img_sizes (list[tuple[int, int]]): List of (H, W) tuples for each feature level.
            img_pos_embeds (list[torch.Tensor] | None): Optional position embeddings for image features.

        Returns:
            Tuple of (encoded_embeddings, attention_mask)
        """
        boxes = geo_prompt.box_embeddings
        boxes_mask = geo_prompt.box_mask
        boxes_labels = geo_prompt.box_labels

        seq_first_img_feats = img_feats[-1]  # [H*W, B, C]
        seq_first_img_pos_embeds = (
            img_pos_embeds[-1] if img_pos_embeds is not None else torch.zeros_like(seq_first_img_feats)
        )

        # Prepare image features for pooling if needed
        if self.points_pool_project or self.boxes_pool_project:
            assert len(img_feats) == len(img_sizes)
            cur_img_feat = img_feats[-1]
            cur_img_feat = self.img_pre_norm(cur_img_feat)
            H, W = img_sizes[-1]
            assert cur_img_feat.shape[0] == H * W
            N, C = cur_img_feat.shape[-2:]
            # Reshape to NxCxHxW
            cur_img_feat = cur_img_feat.permute(1, 2, 0)
            cur_img_feat = cur_img_feat.view(N, C, H, W)
            img_feats = cur_img_feat

        if self.encode_boxes_as_points:
            # Convert boxes to corner points
            assert boxes is not None and boxes.shape[-1] == 4

            boxes_xyxy = xywh2xyxy(boxes)
            top_left, bottom_right = boxes_xyxy.split(split_size=2, dim=-1)

            # Adjust labels for corner points (offset by 2 and 4)
            labels_tl = boxes_labels + 2
            labels_br = boxes_labels + 4

            # Concatenate top-left and bottom-right points
            points = torch.cat([top_left, bottom_right], dim=0)
            points_labels = torch.cat([labels_tl, labels_br], dim=0)
            points_mask = torch.cat([boxes_mask, boxes_mask], dim=1)

            final_embeds, final_mask = self._encode_points(
                points=points,
                points_mask=points_mask,
                points_labels=points_labels,
                img_feats=img_feats,
            )
        else:
            # Encode boxes directly
            final_embeds, final_mask = self._encode_boxes(
                boxes=boxes,
                boxes_mask=boxes_mask,
                boxes_labels=boxes_labels,
                img_feats=img_feats,
            )

        bs = final_embeds.shape[1]
        assert final_mask.shape[0] == bs

        # Add CLS token if configured
        if self.cls_embed is not None:
            cls = self.cls_embed.weight.view(1, 1, self.d_model).repeat(1, bs, 1)
            cls_mask = torch.zeros(bs, 1, dtype=final_mask.dtype, device=final_mask.device)
            final_embeds, final_mask = concat_padded_sequences(final_embeds, final_mask, cls, cls_mask)

        # Final projection
        if self.final_proj is not None:
            final_embeds = self.norm(self.final_proj(final_embeds))

        # Transformer encoding layers
        if self.encode is not None:
            for lay in self.encode:
                final_embeds = lay(
                    tgt=final_embeds,
                    memory=seq_first_img_feats,
                    tgt_key_padding_mask=final_mask,
                    pos=seq_first_img_pos_embeds,
                )
            final_embeds = self.encode_norm(final_embeds)

        return final_embeds, final_mask