def build_outputs(
        self,
        inference_session: Sam3VideoInferenceSession,
        det_out: dict[str, Tensor],
        tracker_low_res_masks_global: Tensor,
        tracker_update_plan: dict,
        reconditioned_obj_ids: set | None = None,
    ):
        """
        Build output dictionary with low-resolution masks.
        Interpolation to video resolution is handled by the processor.

        Returns:
            obj_id_to_mask: dict mapping obj_id to low-res mask tensor (1, H_low, W_low)
        """
        new_det_out_inds: list[int] = tracker_update_plan["new_det_out_inds"]
        new_det_obj_ids: list[int] = tracker_update_plan["new_det_obj_ids"]
        obj_id_to_mask = {}  # obj_id --> low-res mask tensor

        # Part 1: masks from tracker propagation (existing objects)
        existing_masklet_obj_ids = inference_session.obj_ids
        for obj_id, mask in zip(existing_masklet_obj_ids, tracker_low_res_masks_global):
            obj_id_to_mask[int(obj_id)] = mask.unsqueeze(0)  # (1, H_low, W_low)

        # Part 2: masks from new detections
        if len(new_det_out_inds) > 0:
            new_det_out_inds_t = torch.tensor(new_det_out_inds, dtype=torch.long, device=det_out["mask"].device)
            new_det_low_res_masks = det_out["mask"][new_det_out_inds_t]
            # Apply hole filling to new detection masks
            new_det_low_res_masks = fill_holes_in_mask_scores(
                new_det_low_res_masks.unsqueeze(1),
                max_area=self.fill_hole_area,
                fill_holes=True,
                remove_sprinkles=True,
            ).squeeze(1)

            for obj_id, mask in zip(new_det_obj_ids, new_det_low_res_masks):
                obj_id_to_mask[int(obj_id)] = mask.unsqueeze(0)  # (1, H_low, W_low)

        # Part 3: Override masks for reconditioned objects using detection masks
        if reconditioned_obj_ids is not None and len(reconditioned_obj_ids) > 0:
            trk_id_to_max_iou_high_conf_det = tracker_update_plan.get("trk_id_to_max_iou_high_conf_det", {})

            for obj_id in reconditioned_obj_ids:
                det_idx = trk_id_to_max_iou_high_conf_det.get(obj_id)
                if det_idx is not None:
                    det_mask = det_out["mask"][det_idx].unsqueeze(0)  # (1, H_low, W_low)
                    obj_id_to_mask[int(obj_id)] = det_mask

        return obj_id_to_mask