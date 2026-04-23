def _forward_sam_heads(
        self,
        backbone_features,
        point_inputs=None,
        mask_inputs=None,
        high_res_features=None,
        multimask_output=False,
    ):
        """Forward pass through SAM prompt encoders and mask heads.

        This method processes image features and optional point/mask inputs to generate object masks and scores.

        Args:
            backbone_features (torch.Tensor): Image features with shape (B, C, H, W).
            point_inputs (dict[str, torch.Tensor] | None): Dictionary containing point prompts with keys 'point_coords'
                (Tensor of shape (B, P, 2) with float32 dtype, containing absolute pixel-unit coordinates in (x, y)
                format for P input points) and 'point_labels' (Tensor of shape (B, P) with int32 dtype, where 1 means
                positive clicks, 0 means negative clicks, and -1 means padding).
            mask_inputs (torch.Tensor | None): Mask of shape (B, 1, H*16, W*16), float or bool, with the same spatial
                size as the image.
            high_res_features (list[torch.Tensor] | None): List of two feature maps with shapes (B, C, 4*H, 4*W) and (B,
                C, 2*H, 2*W) respectively, used as high-resolution feature maps for SAM decoder.
            multimask_output (bool): If True, output 3 candidate masks and their IoU estimates; if False, output only 1
                mask and its IoU estimate.

        Returns:
            low_res_multimasks (torch.Tensor): Tensor of shape (B, M, H*4, W*4) with SAM output mask logits.
            high_res_multimasks (torch.Tensor): Tensor of shape (B, M, H*16, W*16) with upsampled mask logits.
            ious (torch.Tensor): Tensor of shape (B, M) with estimated IoU for each output mask.
            low_res_masks (torch.Tensor): Tensor of shape (B, 1, H*4, W*4) with the best low-resolution mask.
            high_res_masks (torch.Tensor): Tensor of shape (B, 1, H*16, W*16) with the best high-resolution mask.
            obj_ptr (torch.Tensor): Tensor of shape (B, C) with object pointer vector for the output mask.
            object_score_logits (torch.Tensor): Tensor of shape (B, 1) with object score logits.

        Examples:
            >>> backbone_features = torch.rand(1, 256, 32, 32)
            >>> point_inputs = {"point_coords": torch.rand(1, 2, 2), "point_labels": torch.tensor([[1, 0]])}
            >>> mask_inputs = torch.rand(1, 1, 512, 512)
            >>> results = model._forward_sam_heads(backbone_features, point_inputs, mask_inputs)
            >>> (
            ...     low_res_multimasks,
            ...     high_res_multimasks,
            ...     ious,
            ...     low_res_masks,
            ...     high_res_masks,
            ...     obj_ptr,
            ...     object_score_logits,
            ... ) = results
        """
        B = backbone_features.shape[0]
        device = backbone_features.device
        assert backbone_features.size(1) == self.sam_prompt_embed_dim
        assert backbone_features.size(2) == self.sam_image_embedding_size
        assert backbone_features.size(3) == self.sam_image_embedding_size

        # a) Handle point prompts
        if point_inputs is not None:
            sam_point_coords = point_inputs["point_coords"]
            sam_point_labels = point_inputs["point_labels"]
            assert sam_point_coords.shape[0] == B and sam_point_labels.shape[0] == B
        else:
            # If no points are provide, pad with an empty point (with label -1)
            sam_point_coords = torch.zeros(B, 1, 2, device=device, dtype=backbone_features.dtype)
            sam_point_labels = -torch.ones(B, 1, dtype=torch.int32, device=device)

        # b) Handle mask prompts
        if mask_inputs is not None:
            # If mask_inputs is provided, downsize it into low-res mask input if needed
            # and feed it as a dense mask prompt into the SAM mask encoder
            assert len(mask_inputs.shape) == 4 and mask_inputs.shape[:2] == (B, 1)
            if mask_inputs.shape[-2:] != self.sam_prompt_encoder.mask_input_size:
                sam_mask_prompt = F.interpolate(
                    mask_inputs.to(backbone_features.dtype),
                    size=self.sam_prompt_encoder.mask_input_size,
                    align_corners=False,
                    mode="bilinear",
                    antialias=True,  # use antialias for downsampling
                )
            else:
                sam_mask_prompt = mask_inputs
        else:
            # Otherwise, simply feed None (and SAM's prompt encoder will add
            # a learned `no_mask_embed` to indicate no mask input in this case).
            sam_mask_prompt = None

        sparse_embeddings, dense_embeddings = self.sam_prompt_encoder(
            points=(sam_point_coords, sam_point_labels),
            boxes=None,
            masks=sam_mask_prompt,
        )
        low_res_multimasks, ious, sam_output_tokens, object_score_logits = self.sam_mask_decoder(
            image_embeddings=backbone_features,
            image_pe=self.sam_prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=multimask_output,
            repeat_image=False,  # the image is already batched
            high_res_features=high_res_features,
        )
        if self.pred_obj_scores:
            is_obj_appearing = object_score_logits > 0

            # Spatial memory mask is a *hard* choice between obj and no obj, consistent with actual mask prediction
            low_res_multimasks = torch.where(is_obj_appearing[:, None, None], low_res_multimasks, NO_OBJ_SCORE)

        # convert masks from possibly bfloat16 (or float16) to float32
        # (older PyTorch versions before 2.1 don't support `interpolate` on bf16)
        high_res_multimasks = F.interpolate(
            low_res_multimasks,
            size=(self.image_size, self.image_size),
            mode="bilinear",
            align_corners=False,
        )

        sam_output_token = sam_output_tokens[:, 0]
        if multimask_output:
            # take the best mask prediction (with the highest IoU estimation)
            best_iou_inds = torch.argmax(ious, dim=-1)
            batch_inds = torch.arange(B, device=device)
            low_res_masks = low_res_multimasks[batch_inds, best_iou_inds].unsqueeze(1)
            high_res_masks = high_res_multimasks[batch_inds, best_iou_inds].unsqueeze(1)
            if sam_output_tokens.size(1) > 1:
                sam_output_token = sam_output_tokens[batch_inds, best_iou_inds]
        else:
            low_res_masks, high_res_masks = low_res_multimasks, high_res_multimasks

        # Extract object pointer from the SAM output token (with occlusion handling)
        obj_ptr = self.obj_ptr_proj(sam_output_token)
        if self.pred_obj_scores:
            # Allow *soft* no obj ptr, unlike for masks
            if self.soft_no_obj_ptr:
                lambda_is_obj_appearing = object_score_logits.sigmoid()
            else:
                lambda_is_obj_appearing = is_obj_appearing.to(obj_ptr.dtype)

            if self.fixed_no_obj_ptr:
                obj_ptr = lambda_is_obj_appearing * obj_ptr
            obj_ptr = obj_ptr + (1 - lambda_is_obj_appearing) * self.no_obj_ptr
        return (
            low_res_multimasks,
            high_res_multimasks,
            ious,
            low_res_masks,
            high_res_masks,
            obj_ptr,
            object_score_logits,
        )