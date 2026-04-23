def build_outputs(
        det_out: dict[str, torch.Tensor],
        tracker_low_res_masks_global: torch.Tensor,
        tracker_metadata_prev: dict[str, np.ndarray],
        tracker_update_plan: dict[str, np.ndarray],
        reconditioned_obj_ids: set | None = None,
    ):
        """Build the output masks for the current frame."""
        new_det_fa_inds: np.ndarray = tracker_update_plan["new_det_fa_inds"]
        new_det_obj_ids: np.ndarray = tracker_update_plan["new_det_obj_ids"]
        obj_id_to_mask = {}  # obj_id --> output mask tensor

        # Part 1: masks from previous SAM2 propagation
        existing_masklet_obj_ids = tracker_metadata_prev["obj_ids"]
        existing_masklet_binary = tracker_low_res_masks_global.unsqueeze(1)
        assert len(existing_masklet_obj_ids) == len(existing_masklet_binary)
        for obj_id, mask in zip(existing_masklet_obj_ids, existing_masklet_binary):
            obj_id_to_mask[obj_id] = mask  # (1, H_video, W_video)

        # Part 2: masks from new detections
        new_det_fa_inds_t = torch.from_numpy(new_det_fa_inds)
        new_det_low_res_masks = det_out["mask"][new_det_fa_inds_t].unsqueeze(1)
        assert len(new_det_obj_ids) == len(new_det_low_res_masks)
        for obj_id, mask in zip(new_det_obj_ids, new_det_low_res_masks):
            obj_id_to_mask[obj_id] = mask  # (1, H_video, W_video)

        # Part 3: Override masks for reconditioned objects using detection masks
        if reconditioned_obj_ids is not None and len(reconditioned_obj_ids) > 0:
            trk_id_to_max_iou_high_conf_det = tracker_update_plan.get("trk_id_to_max_iou_high_conf_det", {})

            for obj_id in reconditioned_obj_ids:
                det_idx = trk_id_to_max_iou_high_conf_det.get(obj_id)

                if det_idx is not None:
                    obj_id_to_mask[obj_id] = det_out["mask"][det_idx].unsqueeze(0)

        return obj_id_to_mask