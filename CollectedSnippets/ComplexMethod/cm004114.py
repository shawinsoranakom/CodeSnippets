def _tracker_update_memories(
        self,
        inference_session: Sam3VideoInferenceSession,
        frame_idx: int,
        low_res_masks: Tensor,
        reconditioned_masks: dict[int, Tensor] | None = None,
    ):
        """
        Run Sam3Tracker memory encoder, enforcing non-overlapping constraints globally.
        Now with batched memory encoding for better performance.

        Args:
            inference_session: The inference session state
            frame_idx: Current frame index
            low_res_masks: Low-resolution tracker masks for all objects
            reconditioned_masks: Optional dict of obj_idx -> high_res_mask for objects that
                                should use detection masks instead of tracker masks
        """
        if len(inference_session.obj_ids) == 0:
            return

        if reconditioned_masks is None:
            reconditioned_masks = {}
        # Interpolate tracker masks to high resolution
        high_res_masks = low_res_masks.unsqueeze(1)

        # Override with detection masks for reconditioned objects
        for obj_idx, recond_mask in reconditioned_masks.items():
            high_res_masks[obj_idx] = recond_mask.float()
            # Mark as conditioning frame for reconditioned objects
            output_dict = inference_session.output_dict_per_obj[obj_idx]
            if frame_idx in output_dict["non_cond_frame_outputs"]:
                current_out = output_dict["non_cond_frame_outputs"].pop(frame_idx)
                output_dict["cond_frame_outputs"][frame_idx] = current_out

        # Apply non-overlapping constraints before memory encoding.
        # Constraints are enforced independently per prompt group.
        # Every object ID has a prompt_id assigned when it's created.
        prompt_ids_for_objects = [
            inference_session.obj_id_to_prompt_id[obj_id] for obj_id in inference_session.obj_ids
        ]
        high_res_masks = self._suppress_object_pw_area_shrinkage(high_res_masks, prompt_ids_for_objects)
        # Use mask areas as a proxy for object scores
        object_score_logits = torch.where((high_res_masks > 0).any(dim=(-1, -2)), 10.0, -10.0)

        # Run memory encoder in batch for all objects at once
        num_objects = len(inference_session.obj_ids)
        object_score_logits_batched = object_score_logits.unsqueeze(-1)  # Shape: (num_objects, 1)

        # Encode memories for all objects in one batch call
        maskmem_features_batched, maskmem_pos_enc_batched = self.run_memory_encoder(
            inference_session,
            frame_idx,
            high_res_masks,  # Shape: (num_objects, 1, H, W)
            object_score_logits_batched,  # Shape: (num_objects, 1)
        )

        # Split and store encoded memories per object
        for obj_idx in range(num_objects):
            output_dict = inference_session.output_dict_per_obj[obj_idx]
            # Extract per-object memory from batched result
            maskmem_features = maskmem_features_batched[:, obj_idx : obj_idx + 1]
            maskmem_pos_enc = maskmem_pos_enc_batched[:, obj_idx : obj_idx + 1]

            for storage_key in ["cond_frame_outputs", "non_cond_frame_outputs"]:
                if frame_idx not in output_dict[storage_key]:
                    continue
                current_out = output_dict[storage_key][frame_idx]
                current_out["maskmem_features"] = maskmem_features
                current_out["maskmem_pos_enc"] = maskmem_pos_enc