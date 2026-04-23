def _tracker_update_memories(
        self, tracker_inference_states: list[Any], frame_idx: int, low_res_masks: torch.Tensor
    ):
        """Run Sam2 memory encoder, enforcing non-overlapping constraints globally."""
        if len(tracker_inference_states) == 0:
            return
        # NOTE: inspect this part if we observe OOMs in the demo
        high_res_masks = F.interpolate(
            low_res_masks.unsqueeze(1),
            size=self.interpol_size,
            mode="bilinear",
            align_corners=False,
        )
        # We first apply non-overlapping constraints before memory encoding. This may include some suppression heuristics.
        if not hasattr(self, "_warm_up_complete") or self._warm_up_complete:
            high_res_masks = self.tracker.model._suppress_object_pw_area_shrinkage(high_res_masks)
        # Instead of gathering the predicted object scores, we use mask areas as a proxy.
        object_score_logits = torch.where((high_res_masks > 0).any(dim=(-1, -2)), 10.0, -10.0)

        # Run the memory encoder on local slices for each GPU
        start_idx_gpu = 0
        start_idx_state = start_idx_gpu
        for tracker_state in tracker_inference_states:
            num_obj_per_state = len(tracker_state["obj_ids"])
            if num_obj_per_state == 0:
                continue
            # Get the local high-res masks and object score logits for this inference state
            end_idx_state = start_idx_state + num_obj_per_state
            local_high_res_masks = high_res_masks[start_idx_state:end_idx_state]
            local_object_score_logits = object_score_logits[start_idx_state:end_idx_state]
            local_batch_size = local_high_res_masks.size(0)
            # Run Sam2 memory encoder. Note that we do not re-enforce the non-overlapping constraint as it is turned off by default

            encoded_mem = self.tracker._run_memory_encoder(
                local_batch_size,
                local_high_res_masks,
                local_object_score_logits,
                is_mask_from_pts=False,
                inference_state=tracker_state,
            )
            local_maskmem_features, local_maskmem_pos_enc = encoded_mem
            # Store encoded memories in the local inference state
            output_dict = tracker_state["output_dict"]
            for storage_key in ["cond_frame_outputs", "non_cond_frame_outputs"]:
                if frame_idx not in output_dict[storage_key]:
                    continue
                output_dict[storage_key][frame_idx]["maskmem_features"] = local_maskmem_features
                output_dict[storage_key][frame_idx]["maskmem_pos_enc"] = [pos for pos in local_maskmem_pos_enc]
                # for batched inference state, we also need to add per-object
                # memory slides to support instance interactivity
                self.tracker._add_output_per_object(
                    inference_state=tracker_state,
                    frame_idx=frame_idx,
                    current_out=output_dict[storage_key][frame_idx],
                    storage_key=storage_key,
                )
            start_idx_state += num_obj_per_state