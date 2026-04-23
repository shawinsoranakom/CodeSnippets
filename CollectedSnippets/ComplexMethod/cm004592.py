def forward(
        self,
        image_embeddings: torch.Tensor,
        image_positional_embeddings: torch.Tensor,
        sparse_prompt_embeddings: torch.Tensor,
        dense_prompt_embeddings: torch.Tensor,
        multimask_output: bool,
        hq_token_only: bool,
        intermediate_embeddings: list[torch.Tensor] | None = None,
        attention_similarity: torch.Tensor | None = None,
        target_embedding: torch.Tensor | None = None,
    ) -> SamHQMMaskDecoderOutputs:
        """
        Predict high-quality masks given image and prompt embeddings.

        Args:
            image_embeddings (`torch.Tensor`):
                The embeddings from the image encoder.
            image_positional_embedding (`torch.Tensor`):
                Positional encoding with the shape of image_embeddings.
            sparse_prompt_embeddings (`torch.Tensor`):
                The embeddings of the points and boxes.
            dense_prompt_embeddings (`torch.Tensor`):
                The embeddings of the mask inputs.
            multimask_output (bool):
                Whether to return multiple masks or a single mask.
            hq_token_only (bool):
                Whether to use only the high-quality token output or combine with SAM output.
            intermediate_embeddings (`torch.Tensor`):
                Intermediate embeddings from the vision encoder for feature fusion.
            attention_similarity (`torch.Tensor`, *optional*):
                Optional tensor for attention similarity computation.
            target_embedding (`torch.Tensor`, *optional*):
                Optional target embedding for transformer processing.

        Returns:
            `Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor]]`: A tuple of tensors containing:
                - A tensor of shape `(batch_size, num_prompts, num_masks, height, width)` containing the output masks.
                - A tensor of shape `(batch_size, num_prompts, num_masks)` containing the iou predictions for each mask.
                - (Optional) A tuple containing attention tensors if output_attentions is True.
        """
        batch_size, num_channels, height, width = image_embeddings.shape
        point_batch_size = sparse_prompt_embeddings.shape[1] if sparse_prompt_embeddings is not None else 1

        has_intermediate = intermediate_embeddings is not None and len(intermediate_embeddings) > 0

        if has_intermediate:
            vit_features = intermediate_embeddings[0].permute(0, 3, 1, 2).contiguous()

        embed_encode = self.encoder_conv1(image_embeddings)
        embed_encode = self.activation(self.encoder_norm(embed_encode))
        embed_encode = self.encoder_conv2(embed_encode)

        if has_intermediate:
            compressed_vit_features = self.compress_vit_conv1(vit_features)
            compressed_vit_features = self.activation(self.compress_vit_norm(compressed_vit_features))
            compressed_vit_features = self.compress_vit_conv2(compressed_vit_features)

            hq_features = embed_encode + compressed_vit_features
        else:
            hq_features = embed_encode

        output_tokens = torch.cat([self.iou_token.weight, self.mask_tokens.weight, self.hq_token.weight], dim=0)
        output_tokens = output_tokens.repeat(batch_size, point_batch_size, 1, 1)

        if sparse_prompt_embeddings is not None:
            tokens = torch.cat([output_tokens, sparse_prompt_embeddings], dim=2)
        else:
            tokens = output_tokens
        point_embeddings = tokens.to(self.iou_token.weight.dtype)
        image_embeddings = image_embeddings + dense_prompt_embeddings
        image_embeddings = image_embeddings.repeat_interleave(point_batch_size, 0)
        image_positional_embeddings = image_positional_embeddings.repeat_interleave(point_batch_size, 0)

        point_embedding, iou_token_out = self.transformer(
            point_embeddings=point_embeddings,
            image_embeddings=image_embeddings,
            image_positional_embeddings=image_positional_embeddings,
            attention_similarity=attention_similarity,
            target_embedding=target_embedding,
        )
        iou_token_out = point_embedding[:, :, 0, :]
        mask_tokens_out = point_embedding[:, :, 1 : (1 + self.num_mask_tokens), :]

        image_embeddings = image_embeddings.transpose(2, 3).reshape(
            batch_size * point_batch_size, num_channels, height, width
        )

        upscaled_embedding = self.upscale_conv1(image_embeddings)
        upscaled_embedding = self.activation(self.upscale_layer_norm(upscaled_embedding))
        upscaled_embedding = self.activation(self.upscale_conv2(upscaled_embedding))

        upscaled_embedding_hq = self.mask_conv1(upscaled_embedding)
        upscaled_embedding_hq = self.activation(self.mask_norm(upscaled_embedding_hq))
        upscaled_embedding_hq = self.mask_conv2(upscaled_embedding_hq)

        if hq_features.shape[0] == 1:
            hq_features = hq_features.repeat(batch_size * point_batch_size, 1, 1, 1)
        elif hq_features.shape[0] == batch_size and batch_size * point_batch_size != batch_size:
            hq_features = hq_features.repeat_interleave(point_batch_size, 0)
        upscaled_embedding_hq = upscaled_embedding_hq + hq_features

        hyper_in_list = []
        for mask_token_index in range(self.num_mask_tokens):
            if mask_token_index < self.num_mask_tokens - 1:
                current_mlp = self.output_hypernetworks_mlps[mask_token_index]
            else:
                current_mlp = self.hq_mask_mlp
            hyper_in_list += [current_mlp(mask_tokens_out[:, :, mask_token_index, :])]

        hyper_in = torch.stack(hyper_in_list, dim=2)
        _, num_channels, height, width = upscaled_embedding.shape
        upscaled_embedding = upscaled_embedding.reshape(batch_size, point_batch_size, num_channels, height * width)
        upscaled_embedding_hq = upscaled_embedding_hq.reshape(
            batch_size, point_batch_size, num_channels, height * width
        )

        masks_sam = (hyper_in[:, :, : self.num_mask_tokens - 1] @ upscaled_embedding).reshape(
            batch_size, point_batch_size, -1, height, width
        )
        masks_hq = (hyper_in[:, :, self.num_mask_tokens - 1 :] @ upscaled_embedding_hq).reshape(
            batch_size, point_batch_size, -1, height, width
        )
        masks = torch.cat([masks_sam, masks_hq], dim=2)

        iou_pred = self.iou_prediction_head(iou_token_out)

        if multimask_output:
            mask_slice = slice(1, self.num_mask_tokens - 1)
            iou_pred = iou_pred[:, :, mask_slice]
            # Sort the IoU scores in descending order and get indices
            iou_pred_sorted, sort_indices = torch.sort(iou_pred, dim=2, descending=True)
            # Reorder the masks according to sorted scores
            masks_sam = masks[:, :, mask_slice, :, :]
            masks_sam = torch.gather(
                masks_sam,
                2,
                sort_indices[..., None, None].expand(-1, -1, -1, masks_sam.shape[3], masks_sam.shape[4]),
            )
            # Update iou_pred with sorted scores
            iou_pred = iou_pred_sorted
        else:
            mask_slice = slice(0, 1)
            iou_pred = iou_pred[:, :, mask_slice]
            masks_sam = masks[:, :, mask_slice, :, :]

        masks_hq = masks[:, :, slice(self.num_mask_tokens - 1, self.num_mask_tokens), :, :]
        if hq_token_only:
            masks = masks_hq
        else:
            masks = masks_sam + masks_hq

        return masks, iou_pred