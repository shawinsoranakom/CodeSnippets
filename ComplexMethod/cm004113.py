def _suppress_overlapping_based_on_recent_occlusion(
        self,
        inference_session: Sam3VideoInferenceSession,
        frame_idx: int,
        tracker_low_res_masks_global: Tensor,
        tracker_metadata_new: dict[str, Any],
        obj_ids_newly_removed: set[int],
        reverse: bool = False,
    ):
        """
        Suppress overlapping masks based on the most recent occlusion information. If an object is removed by hotstart, we always suppress it if it overlaps with any other object.
        Args:
            frame_idx (int): The current frame index.
            tracker_low_res_masks_global (Tensor): The low-resolution masks for the current frame.
            tracker_metadata_prev (Dict[str, Any]): The metadata from the previous frame.
            tracker_metadata_new (Dict[str, Any]): The metadata for the current frame.
            obj_ids_newly_removed (Set[int]): The object IDs that have been removed.
        Return:
            Tensor: The updated low-resolution masks with some objects suppressed.
        """
        obj_ids_global = inference_session.obj_ids
        binary_tracker_low_res_masks_global = tracker_low_res_masks_global > 0
        batch_size = tracker_low_res_masks_global.size(0)
        if batch_size > 0:
            NEVER_OCCLUDED = -1
            ALWAYS_OCCLUDED = 100000  # This value should be larger than any possible frame index, indicates that the object was removed by hotstart logic
            last_occluded_prev = torch.cat(
                [
                    inference_session.obj_id_to_last_occluded.get(
                        obj_id,
                        torch.full(
                            (1,),
                            fill_value=(NEVER_OCCLUDED if obj_id not in obj_ids_newly_removed else ALWAYS_OCCLUDED),
                            device=binary_tracker_low_res_masks_global.device,
                            dtype=torch.long,
                        ),
                    )
                    for obj_id in obj_ids_global
                ],
                dim=0,
            )

            prompt_ids_global = torch.tensor(
                [inference_session.obj_id_to_prompt_id[obj_id] for obj_id in obj_ids_global],
                device=binary_tracker_low_res_masks_global.device,
                dtype=torch.long,
            )
            to_suppress = torch.zeros(
                batch_size,
                device=binary_tracker_low_res_masks_global.device,
                dtype=torch.bool,
            )

            # Only suppress overlaps within the same prompt group.
            unique_prompts = prompt_ids_global.unique(sorted=True)
            for prompt_id in unique_prompts:
                prompt_mask = prompt_ids_global == prompt_id
                prompt_indices = torch.nonzero(prompt_mask, as_tuple=True)[0]
                if prompt_indices.numel() <= 1:
                    continue

                prompt_masks = binary_tracker_low_res_masks_global[prompt_indices]
                prompt_last_occ = last_occluded_prev[prompt_indices]
                prompt_obj_ids = [obj_ids_global[idx] for idx in prompt_indices.tolist()]
                prompt_suppress = self._get_objects_to_suppress_based_on_most_recently_occluded(
                    prompt_masks,
                    prompt_last_occ,
                    prompt_obj_ids,
                    reverse,
                )
                to_suppress[prompt_indices] = prompt_suppress

            # Update metadata with occlusion information
            is_obj_occluded = ~(binary_tracker_low_res_masks_global.any(dim=(-1, -2)))
            is_obj_occluded_or_suppressed = is_obj_occluded | to_suppress
            last_occluded_new = last_occluded_prev.clone()
            last_occluded_new[is_obj_occluded_or_suppressed] = frame_idx
            # Slice out the last occluded frame for each object
            tracker_metadata_new["obj_id_to_last_occluded"] = {
                obj_id: last_occluded_new[obj_idx : obj_idx + 1] for obj_idx, obj_id in enumerate(obj_ids_global)
            }

            # Zero out suppressed masks before memory encoding
            NO_OBJ_LOGIT = -10
            tracker_low_res_masks_global[to_suppress] = NO_OBJ_LOGIT

        return tracker_low_res_masks_global