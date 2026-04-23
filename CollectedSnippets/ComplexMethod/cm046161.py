def add_new_prompts(
        self,
        obj_id,
        points=None,
        labels=None,
        masks=None,
        frame_idx=0,
        inference_state: dict[str, Any] | None = None,
    ):
        """Add new points or masks to a specific frame for a given object ID.

        This method updates the inference state with new prompts (points or masks) for a specified object and frame
        index. It ensures that the prompts are either points or masks, but not both, and updates the internal state
        accordingly. It also handles the generation of new segmentations based on the provided prompts and the existing
        state.

        Args:
            obj_id (int): The ID of the object to which the prompts are associated.
            points (torch.Tensor, optional): The coordinates of the points of interest.
            labels (torch.Tensor, optional): The labels corresponding to the points.
            masks (torch.Tensor, optional): Binary masks for the object.
            frame_idx (int, optional): The index of the frame to which the prompts are applied.
            inference_state (dict[str, Any], optional): The current inference state. If None, uses the instance's
                inference state.

        Returns:
            pred_masks (torch.Tensor): The flattened predicted masks.
            pred_scores (torch.Tensor): A tensor of ones indicating the number of objects.

        Raises:
            AssertionError: If both `masks` and `points` are provided, or neither is provided.

        Notes:
            - Only one type of prompt (either points or masks) can be added per call.
            - If the frame is being tracked for the first time, it is treated as an initial conditioning frame.
            - The method handles the consolidation of outputs and resizing of masks to the original video resolution.
        """
        inference_state = inference_state or self.inference_state
        assert (masks is None) ^ (points is None), "'masks' and 'points' prompts are not compatible with each other."
        obj_idx = self._obj_id_to_idx(obj_id, inference_state)

        point_inputs = None
        pop_key = "point_inputs_per_obj"
        if points is not None:
            point_inputs = {"point_coords": points, "point_labels": labels}
            inference_state["point_inputs_per_obj"][obj_idx][frame_idx] = point_inputs
            pop_key = "mask_inputs_per_obj"
        inference_state["mask_inputs_per_obj"][obj_idx][frame_idx] = masks
        inference_state[pop_key][obj_idx].pop(frame_idx, None)
        # If this frame hasn't been tracked before, we treat it as an initial conditioning
        # frame, meaning that the inputs points are to generate segments on this frame without
        # using any memory from other frames, like in SAM. Otherwise (if it has been tracked),
        # the input points will be used to correct the already tracked masks.
        is_init_cond_frame = frame_idx not in inference_state["frames_already_tracked"]
        obj_output_dict = inference_state["output_dict_per_obj"][obj_idx]
        obj_temp_output_dict = inference_state["temp_output_dict_per_obj"][obj_idx]
        # Add a frame to conditioning output if it's an initial conditioning frame or
        # if the model sees all frames receiving clicks/mask as conditioning frames.
        is_cond = is_init_cond_frame or self.model.add_all_frames_to_correct_as_cond
        storage_key = "cond_frame_outputs" if is_cond else "non_cond_frame_outputs"

        # Get any previously predicted mask logits on this object and feed it along with
        # the new clicks into the SAM mask decoder.
        prev_sam_mask_logits = None
        # lookup temporary output dict first, which contains the most recent output
        # (if not found, then lookup conditioning and non-conditioning frame output)
        if point_inputs is not None:
            prev_out = (
                obj_temp_output_dict[storage_key].get(frame_idx)
                or obj_output_dict["cond_frame_outputs"].get(frame_idx)
                or obj_output_dict["non_cond_frame_outputs"].get(frame_idx)
            )

            if prev_out is not None and prev_out.get("pred_masks") is not None:
                prev_sam_mask_logits = prev_out["pred_masks"].to(
                    device=self.device, non_blocking=self.device.type == "cuda"
                )
                # Clamp the scale of prev_sam_mask_logits to avoid rare numerical issues.
                prev_sam_mask_logits.clamp_(-32.0, 32.0)
        current_out = self._run_single_frame_inference(
            output_dict=obj_output_dict,  # run on the slice of a single object
            frame_idx=frame_idx,
            batch_size=1,  # run on the slice of a single object
            is_init_cond_frame=is_init_cond_frame,
            point_inputs=point_inputs,
            mask_inputs=masks,
            reverse=False,
            # Skip the memory encoder when adding clicks or mask. We execute the memory encoder
            # at the beginning of `propagate_in_video` (after user finalize their clicks). This
            # allows us to enforce non-overlapping constraints on all objects before encoding
            # them into memory.
            run_mem_encoder=False,
            prev_sam_mask_logits=prev_sam_mask_logits,
            inference_state=inference_state,
        )
        # Add the output to the output dict (to be used as future memory)
        obj_temp_output_dict[storage_key][frame_idx] = current_out

        # Resize the output mask to the original video resolution
        consolidated_out = self._consolidate_temp_output_across_obj(
            frame_idx,
            is_cond=is_cond,
            run_mem_encoder=False,
            inference_state=inference_state,
        )
        pred_masks = consolidated_out["pred_masks"].flatten(0, 1)
        return pred_masks.flatten(0, 1), torch.ones(1, dtype=pred_masks.dtype, device=pred_masks.device)