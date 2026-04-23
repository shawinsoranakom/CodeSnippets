def _run_single_frame_inference(
        self,
        inference_session: Sam2VideoInferenceSession,
        frame_idx: int,
        obj_idx: int,
        batch_size: int,
        is_init_cond_frame: bool,
        point_inputs: torch.Tensor | None,
        mask_inputs: torch.Tensor | None,
        reverse: bool,
        prev_sam_mask_logits: torch.Tensor | None = None,
        streaming: bool = False,
    ) -> dict[str, Any]:
        """
        Perform a single tracking step for video object segmentation.

        Args:
            inference_session (`Sam2VideoInferenceSession`):
                The video inference session object.
            frame_idx (`int`):
                Index of the current frame.
            obj_idx (`int`):
                Index of the current object.
            batch_size (`int`):
                Batch size of the current frame.
            is_init_cond_frame (`bool`):
                Whether this is an initial conditioning frame with user inputs.
            point_inputs (`dict`, *optional*):
                Point prompt inputs for the current frame.
            mask_inputs (`torch.Tensor`, *optional*):
                Mask prompt inputs for the current frame.
            reverse (`bool`, *optional*, defaults to `False`):
                Whether to track in reverse time order.
            prev_sam_mask_logits (`torch.Tensor`, *optional*):
                Previously predicted SAM mask logits that can be fed with new clicks.
            streaming (`bool`, *optional*, defaults to `False`):
                Whether this is streaming inference.

        Returns:
            `dict`: Dictionary containing the tracking results for the current frame, including:
                - pred_masks: Predicted low-resolution masks.
                - object_pointer: Object pointer for memory.
                - high_res_masks: High-resolution masks for batched memory encoding.
                - object_score_logits: Object score logits (inference only).
        """
        # Retrieve correct image features
        current_vision_feats, current_vision_pos_embeds = self._prepare_vision_features(
            inference_session, frame_idx, batch_size
        )
        # point and mask should not appear as input simultaneously on the same frame
        if point_inputs is not None and mask_inputs is not None:
            raise ValueError(
                "point_inputs and mask_inputs should not appear as input simultaneously on the same frame"
            )
        # High-resolution feature maps for the SAM head, reshape (HW)BC => BCHW
        if len(current_vision_feats) > 1:
            high_res_features = [
                x.permute(1, 2, 0).view(x.size(1), x.size(2), *s)
                for x, s in zip(current_vision_feats[:-1], self.backbone_feature_sizes[:-1])
            ]
        else:
            high_res_features = None
        if mask_inputs is not None:
            # We directly output the mask input (see it as a GT mask) without using a SAM prompt encoder + mask decoder.
            pix_feat = current_vision_feats[-1].permute(1, 2, 0)
            pix_feat = pix_feat.view(-1, self.hidden_dim, *self.backbone_feature_sizes[-1])
            sam_outputs = self._use_mask_as_output(pix_feat, high_res_features, mask_inputs)
        else:
            # fused the visual feature with previous memory features in the memory bank
            pix_feat = self._prepare_memory_conditioned_features(
                inference_session=inference_session,
                frame_idx=frame_idx,
                obj_idx=obj_idx,
                is_initial_conditioning_frame=is_init_cond_frame,
                current_vision_features=current_vision_feats[-1],
                current_vision_positional_embeddings=current_vision_pos_embeds[-1],
                num_total_frames=inference_session.num_frames,
                track_in_reverse_time=reverse,
                streaming=streaming,
            )
            # apply SAM-style segmentation head
            # here we might feed previously predicted low-res SAM mask logits into the SAM mask decoder,
            # e.g. in demo where such logits come from earlier interaction instead of correction sampling
            # (in this case, any `mask_inputs` shouldn't reach here as they are sent to _use_mask_as_output instead)
            if prev_sam_mask_logits is not None:
                mask_inputs = prev_sam_mask_logits
            multimask_output = self._use_multimask(is_init_cond_frame, point_inputs)
            sam_outputs = self._single_frame_forward(
                pixel_values=None,  # Vision features already computed
                input_points=point_inputs["point_coords"] if point_inputs is not None else None,
                input_labels=point_inputs["point_labels"] if point_inputs is not None else None,
                input_masks=mask_inputs,
                image_embeddings=high_res_features + [pix_feat],
                multimask_output=multimask_output,
            )

        # Memory encoding is now handled in batch by the caller (forward method)
        current_out = {
            "pred_masks": sam_outputs.pred_masks,
            "object_pointer": sam_outputs.object_pointer,
            "high_res_masks": sam_outputs.high_res_masks,  # Needed for batched memory encoding
        }
        if not self.training:
            current_out["object_score_logits"] = sam_outputs.object_score_logits

        return current_out