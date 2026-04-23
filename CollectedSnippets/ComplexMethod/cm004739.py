def forward(
        self,
        inference_session: Sam3TrackerVideoInferenceSession,
        frame_idx: int | None = None,
        frame: torch.Tensor | None = None,
        reverse: bool = False,
        run_mem_encoder: bool = True,
        **kwargs,
    ) -> Sam3TrackerVideoSegmentationOutput:
        r"""
        inference_session (`Sam3TrackerVideoInferenceSession`):
            The video inference session object.
        frame_idx (`int`, *optional*):
            The index of the frame on which to run inference. No need to provide when inferring
            on a new streamed frame.
        frame (`torch.Tensor`, *optional*):
            The frame to process. Provide when streaming.
        reverse (`bool`, *optional*, defaults to `False`):
            Whether to propagate in reverse.
        run_mem_encoder (`bool`, *optional*, defaults to `True`):
            Whether to run the memory encoder on predicted masks. The memory encoder is batched across all objects for efficiency.
        """
        if frame is not None:
            frame_idx = inference_session.add_new_frame(frame, frame_idx)

        if frame is not None and inference_session.get_obj_num() == 0:
            raise ValueError("No objects are provided for tracking; please add inputs first.")

        num_objects = inference_session.get_obj_num()
        pred_masks_per_obj = [None] * num_objects
        object_score_logits_per_obj = [None] * num_objects

        # Collect data for batched memory encoding
        objects_needing_memory_encoding = []
        high_res_masks_for_memory = []
        object_score_logits_for_memory = []
        is_mask_from_pts_per_obj = []

        # Note: We avoid batched inference here because per-object inputs (clicks/masks)
        # can differ across objects.
        for obj_idx in range(num_objects):
            obj_id = inference_session.obj_idx_to_id(obj_idx)
            has_new_inputs = obj_id in inference_session.obj_with_new_inputs
            has_cond_output = frame_idx in inference_session.output_dict_per_obj[obj_idx]["cond_frame_outputs"]
            # If this object has no new inputs and this frame already has a
            # conditioning output, reuse the cached masks instead of recomputing.
            if (not has_new_inputs) and has_cond_output:
                pred_masks = inference_session.get_output(obj_idx, frame_idx, "pred_masks", is_conditioning_frame=True)
                object_score_logits = inference_session.get_output(
                    obj_idx, frame_idx, "object_score_logits", is_conditioning_frame=True
                )
                is_init_cond_frame = True
            else:
                # Defaults when there are no new inputs
                is_init_cond_frame = False
                point_inputs = None
                mask_inputs = None

                if has_new_inputs:
                    is_init_cond_frame = frame_idx not in inference_session.frames_tracked_per_obj[obj_idx]
                    if is_init_cond_frame:
                        reverse = False
                    point_inputs = inference_session.point_inputs_per_obj[obj_idx].get(frame_idx, None)
                    mask_inputs = inference_session.mask_inputs_per_obj[obj_idx].get(frame_idx, None)
                    if point_inputs is not None or mask_inputs is not None:
                        inference_session.obj_with_new_inputs.remove(obj_id)

                current_out = self._run_single_frame_inference(
                    inference_session=inference_session,
                    obj_idx=obj_idx,
                    frame_idx=frame_idx,
                    batch_size=1,  # run on the slice of a single object
                    is_init_cond_frame=is_init_cond_frame,
                    point_inputs=point_inputs,
                    mask_inputs=mask_inputs,
                    reverse=reverse,
                    streaming=frame is not None,
                )
                inference_session.store_output(
                    obj_idx, frame_idx, output_value=current_out, is_conditioning_frame=is_init_cond_frame
                )
                pred_masks = current_out["pred_masks"]
                object_score_logits = current_out["object_score_logits"]

                # Collect data for batched memory encoding
                if run_mem_encoder and self.num_maskmem > 0:
                    objects_needing_memory_encoding.append(obj_idx)
                    high_res_masks_for_memory.append(current_out["high_res_masks"])
                    object_score_logits_for_memory.append(object_score_logits)
                    is_mask_from_pts_per_obj.append(point_inputs is not None or mask_inputs is not None)

            pred_masks_per_obj[obj_idx] = pred_masks
            object_score_logits_per_obj[obj_idx] = object_score_logits.squeeze(-1)
            if not is_init_cond_frame:
                # only for tracked frames, not for initial conditioning frames
                inference_session.frames_tracked_per_obj[obj_idx][frame_idx] = {"reverse": reverse}

        # Batch encode memories for all objects at once
        self._batch_encode_memories(
            inference_session=inference_session,
            frame_idx=frame_idx,
            objects_needing_memory_encoding=objects_needing_memory_encoding,
            high_res_masks_for_memory=high_res_masks_for_memory,
            object_score_logits_for_memory=object_score_logits_for_memory,
            is_mask_from_pts_per_obj=is_mask_from_pts_per_obj,
        )

        # Resize the output mask to the original video resolution (we directly use
        # the mask scores on GPU for output to avoid any CPU conversion in between)
        if len(pred_masks_per_obj) > 1:
            all_pred_masks = torch.cat(pred_masks_per_obj, dim=0)
            all_object_score_logits = torch.cat(object_score_logits_per_obj, dim=0)
        else:
            all_pred_masks = pred_masks_per_obj[0]
            all_object_score_logits = object_score_logits_per_obj[0]

        return Sam3TrackerVideoSegmentationOutput(
            object_ids=inference_session.obj_ids.copy(),
            pred_masks=all_pred_masks,
            object_score_logits=all_object_score_logits,
            frame_idx=frame_idx,
        )