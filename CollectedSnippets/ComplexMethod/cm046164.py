def _consolidate_temp_output_across_obj(
        self,
        frame_idx,
        is_cond=False,
        run_mem_encoder=False,
        inference_state: dict[str, Any] | None = None,
    ):
        """Consolidate per-object temporary outputs into a single output for all objects.

        This method combines the temporary outputs for each object on a given frame into a unified
        output. It fills in any missing objects either from the main output dictionary or leaves
        placeholders if they do not exist in the main output. Optionally, it can re-run the memory encoder after
        applying non-overlapping constraints to the object scores.

        Args:
            frame_idx (int): The index of the frame for which to consolidate outputs.
            is_cond (bool, optional): Indicates if the frame is considered a conditioning frame.
            run_mem_encoder (bool, optional): Specifies whether to run the memory encoder after consolidating the
                outputs.
            inference_state (dict[str, Any], optional): The current inference state. If None, uses the instance's
                inference state.

        Returns:
            (dict): A consolidated output dictionary containing the combined results for all objects.

        Notes:
            - The method initializes the consolidated output with placeholder values for missing objects.
            - It searches for outputs in both the temporary and main output dictionaries.
            - If `run_mem_encoder` is True, it applies non-overlapping constraints and re-runs the memory encoder.
            - The `maskmem_features` and `maskmem_pos_enc` are only populated when `run_mem_encoder` is True.
        """
        inference_state = inference_state or self.inference_state
        batch_size = len(inference_state["obj_idx_to_id"])
        storage_key = "cond_frame_outputs" if is_cond else "non_cond_frame_outputs"

        # Initialize `consolidated_out`. Its "maskmem_features" and "maskmem_pos_enc"
        # will be added when rerunning the memory encoder after applying non-overlapping
        # constraints to object scores. Its "pred_masks" are prefilled with a large
        # negative value (NO_OBJ_SCORE) to represent missing objects.
        consolidated_out = {
            "maskmem_features": None,
            "maskmem_pos_enc": None,
            "pred_masks": torch.full(
                # size=(batch_size, 1, self.imgsz[0] // 4, self.imgsz[1] // 4),
                size=(batch_size, 1, *self._bb_feat_sizes[0]),
                fill_value=-1024.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
            "obj_ptr": torch.full(
                size=(batch_size, self.model.hidden_dim),
                fill_value=-1024.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
            "object_score_logits": torch.full(
                size=(batch_size, 1),
                # default to 10.0 for object_score_logits, i.e. assuming the object is
                # present as sigmoid(10)=1, same as in `predict_masks` of `MaskDecoder`
                fill_value=10.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
        }
        for obj_idx in range(batch_size):
            obj_temp_output_dict = inference_state["temp_output_dict_per_obj"][obj_idx]
            obj_output_dict = inference_state["output_dict_per_obj"][obj_idx]
            out = (
                obj_temp_output_dict[storage_key].get(frame_idx)
                # If the object doesn't appear in "temp_output_dict_per_obj" on this frame,
                # we fall back and look up its previous output in "output_dict_per_obj".
                # We look up both "cond_frame_outputs" and "non_cond_frame_outputs" in
                # "output_dict_per_obj" to find a previous output for this object.
                or obj_output_dict["cond_frame_outputs"].get(frame_idx)
                or obj_output_dict["non_cond_frame_outputs"].get(frame_idx)
            )
            # If the object doesn't appear in "output_dict_per_obj" either, we skip it
            # and leave its mask scores to the default scores (i.e. the NO_OBJ_SCORE
            # placeholder above) and set its object pointer to be a dummy pointer.
            if out is None:
                # Fill in dummy object pointers for those objects without any inputs or
                # tracking outcomes on this frame (only do it under `run_mem_encoder=True`,
                # i.e. when we need to build the memory for tracking).
                if run_mem_encoder:
                    # fill object pointer with a dummy pointer (based on an empty mask)
                    consolidated_out["obj_ptr"][obj_idx : obj_idx + 1] = self._get_empty_mask_ptr(frame_idx)
                continue
            # Add the temporary object output mask to consolidated output mask
            consolidated_out["pred_masks"][obj_idx : obj_idx + 1] = out["pred_masks"]
            consolidated_out["obj_ptr"][obj_idx : obj_idx + 1] = out["obj_ptr"]

        # Optionally, apply non-overlapping constraints on the consolidated scores and rerun the memory encoder
        if run_mem_encoder:
            high_res_masks = F.interpolate(
                consolidated_out["pred_masks"],
                size=self.imgsz,
                mode="bilinear",
                align_corners=False,
            )
            if self.model.non_overlap_masks_for_mem_enc:
                high_res_masks = self.model._apply_non_overlapping_constraints(high_res_masks)
            consolidated_out["maskmem_features"], consolidated_out["maskmem_pos_enc"] = self._run_memory_encoder(
                batch_size=batch_size,
                high_res_masks=high_res_masks,
                is_mask_from_pts=True,  # these frames are what the user interacted with
                object_score_logits=consolidated_out["object_score_logits"],
                inference_state=inference_state,
            )

        return consolidated_out