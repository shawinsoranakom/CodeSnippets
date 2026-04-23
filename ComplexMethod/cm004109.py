def postprocess_outputs(
        self,
        inference_session,
        model_outputs,
        original_sizes: list[list[float]] | torch.Tensor | None = None,
    ):
        """
        Post-process model outputs to get final masks, boxes, and scores.

        Args:
            inference_session (`Sam3VideoInferenceSession`):
                The inference session object.
            model_outputs (`Sam3VideoSegmentationOutput`):
                The raw model output from `Sam3VideoModel.forward()`.
            original_sizes (`list[list[float]]` or `torch.Tensor`, *optional*):
                Optional original frame sizes [height, width]. Required for streaming inference
                when video_height/video_width are not set in the session.

        Returns:
            `dict`: A dictionary containing the following keys:
                - **object_ids** (`torch.Tensor` of shape `(num_objects,)`): Object IDs for each detected object.
                - **scores** (`torch.Tensor` of shape `(num_objects,)`): Detection scores for each object.
                - **boxes** (`torch.Tensor` of shape `(num_objects, 4)`): Bounding boxes in XYXY format
                  (top_left_x, top_left_y, bottom_right_x, bottom_right_y).
                - **masks** (`torch.Tensor` of shape `(num_objects, height, width)`): Binary segmentation masks
                  for each object at the original video resolution.
                - **prompt_to_obj_ids** (`dict[str, list[int]]`): Mapping from prompt text to list of
                  object IDs detected by that prompt.
        """
        obj_id_to_mask = model_outputs["obj_id_to_mask"]  # low res masks (1, H_low, W_low)
        curr_obj_ids = sorted(obj_id_to_mask.keys())

        # Get video dimensions - use original_sizes for streaming inference if session doesn't have them
        if inference_session.video_height is not None and inference_session.video_width is not None:
            H_video, W_video = inference_session.video_height, inference_session.video_width
        elif original_sizes is not None:
            if isinstance(original_sizes, torch.Tensor):
                original_sizes = original_sizes.cpu().tolist()
            # original_sizes is a list of [height, width] pairs, take the first one
            if isinstance(original_sizes[0], list):
                H_video, W_video = int(original_sizes[0][0]), int(original_sizes[0][1])
            else:
                H_video, W_video = int(original_sizes[0]), int(original_sizes[1])
        else:
            raise ValueError(
                "Either inference_session.video_height/video_width must be set, "
                "or original_sizes must be provided for streaming inference."
            )
        if len(curr_obj_ids) == 0:
            out_obj_ids = torch.zeros(0, dtype=torch.int64)
            out_probs = torch.zeros(0, dtype=torch.float32)
            out_binary_masks = torch.zeros(0, H_video, W_video, dtype=torch.bool)
            out_boxes_xyxy = torch.zeros(0, 4, dtype=torch.float32)
        else:
            out_obj_ids = torch.tensor(curr_obj_ids, dtype=torch.int64)
            out_probs = torch.tensor([model_outputs["obj_id_to_score"][obj_id] for obj_id in curr_obj_ids])
            out_tracker_probs = torch.tensor(
                [model_outputs["obj_id_to_tracker_score"].get(obj_id, 0.0) for obj_id in curr_obj_ids]
            )

            # Interpolate low-res masks to video resolution
            low_res_masks = torch.cat([obj_id_to_mask[obj_id] for obj_id in curr_obj_ids], dim=0)  # (N, H_low, W_low)
            # Add channel dimension for interpolation: (N, H, W) -> (N, 1, H, W)
            out_binary_masks = torch.nn.functional.interpolate(
                low_res_masks.unsqueeze(1),
                size=(H_video, W_video),
                mode="bilinear",
                align_corners=False,
            ).squeeze(1)  # (N, H_video, W_video)
            out_binary_masks = out_binary_masks > 0

            assert out_binary_masks.dtype == torch.bool
            keep = out_binary_masks.any(dim=(1, 2)).cpu()  # remove masks with 0 areas
            # hide outputs for those object IDs in `obj_ids_to_hide`
            obj_ids_to_hide = []
            if model_outputs["suppressed_obj_ids"] is not None:
                obj_ids_to_hide.extend(list(model_outputs["suppressed_obj_ids"]))
            if len(inference_session.hotstart_removed_obj_ids) > 0:
                obj_ids_to_hide.extend(list(inference_session.hotstart_removed_obj_ids))
            if len(obj_ids_to_hide) > 0:
                obj_ids_to_hide_t = torch.tensor(obj_ids_to_hide, dtype=torch.int64)
                keep &= ~torch.isin(out_obj_ids, obj_ids_to_hide_t)

            # slice those valid entries from the original outputs
            keep_idx = torch.nonzero(keep, as_tuple=True)[0]
            keep_idx_gpu = keep_idx.to(device=out_binary_masks.device, non_blocking=True)

            out_obj_ids = torch.index_select(out_obj_ids, 0, keep_idx)
            out_probs = torch.index_select(out_probs, 0, keep_idx)
            out_tracker_probs = torch.index_select(out_tracker_probs, 0, keep_idx)
            out_binary_masks = torch.index_select(out_binary_masks, 0, keep_idx_gpu)

            out_boxes_xyxy = masks_to_boxes(out_binary_masks)

        # Apply non-overlapping constraints on the existing masklets.
        # Constraints are enforced independently per prompt group.
        if out_binary_masks.shape[0] > 1:
            assert len(out_binary_masks) == len(out_tracker_probs)
            prompt_ids_filtered = [
                inference_session.obj_id_to_prompt_id[int(obj_id)] for obj_id in out_obj_ids.tolist()
            ]
            out_binary_masks = (
                self._apply_object_wise_non_overlapping_constraints(
                    out_binary_masks.unsqueeze(1),
                    out_tracker_probs.unsqueeze(1).to(out_binary_masks.device),
                    background_value=0,
                    prompt_ids=prompt_ids_filtered,
                ).squeeze(1)
            ) > 0

        # Build prompt_to_obj_ids mapping: group object IDs by their associated prompt text.
        prompt_to_obj_ids = {}
        for obj_id in out_obj_ids.tolist():
            prompt_id = inference_session.obj_id_to_prompt_id[obj_id]
            prompt_text = inference_session.prompts[prompt_id]
            prompt_to_obj_ids.setdefault(prompt_text, []).append(obj_id)

        outputs = {
            "object_ids": out_obj_ids,
            "scores": out_probs,
            "boxes": out_boxes_xyxy,
            "masks": out_binary_masks,
            "prompt_to_obj_ids": prompt_to_obj_ids,
        }
        return outputs