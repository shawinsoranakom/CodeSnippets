def update_memory(
        self,
        obj_ids: list[int] | None = None,
        points: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        masks: torch.Tensor | None = None,
    ) -> None:
        """Append the imgState to the memory_bank and update the memory for the model.

        Args:
            obj_ids (list[int]): List of object IDs corresponding to the prompts.
            points (torch.Tensor | None): Tensor of shape (B, N, 2) representing the input points for N objects.
            labels (torch.Tensor | None): Tensor of shape (B, N) representing the labels for the input points.
            masks (torch.Tensor | None): Optional tensor of shape (N, H, W) representing the input masks for N objects.
        """
        consolidated_out = {
            "maskmem_features": None,
            "maskmem_pos_enc": None,
            "pred_masks": torch.full(
                size=(self._max_obj_num, 1, self.imgsz[0] // 4, self.imgsz[1] // 4),
                fill_value=-1024.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
            "obj_ptr": torch.full(
                size=(self._max_obj_num, self.model.hidden_dim),
                fill_value=-1024.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
            "object_score_logits": torch.full(
                size=(self._max_obj_num, 1),
                # default to 10.0 for object_score_logits, i.e. assuming the object is
                # present as sigmoid(10)=1, same as in `predict_masks` of `MaskDecoder`
                fill_value=-32,  # 10.0,
                dtype=self.torch_dtype,
                device=self.device,
            ),
        }

        for i, obj_id in enumerate(obj_ids):
            assert obj_id < self._max_obj_num
            obj_idx = self._obj_id_to_idx(int(obj_id))
            self.obj_idx_set.add(obj_idx)
            point, label = points[[i]], labels[[i]]
            mask = masks[[i]][None] if masks is not None else None
            # Currently, only bbox prompt or mask prompt is supported, so we assert that bbox is not None.
            assert point is not None or mask is not None, "Either bbox, points or mask is required"
            out = self.track_step(obj_idx, point, label, mask)
            if out is not None:
                obj_mask = out["pred_masks"]
                assert obj_mask.shape[-2:] == consolidated_out["pred_masks"].shape[-2:], (
                    f"Expected mask shape {consolidated_out['pred_masks'].shape[-2:]} but got {obj_mask.shape[-2:]} for object {obj_idx}."
                )
                consolidated_out["pred_masks"][obj_idx : obj_idx + 1] = obj_mask
                consolidated_out["obj_ptr"][obj_idx : obj_idx + 1] = out["obj_ptr"]

                if "object_score_logits" in out.keys():
                    consolidated_out["object_score_logits"][obj_idx : obj_idx + 1] = out["object_score_logits"]

        high_res_masks = F.interpolate(
            consolidated_out["pred_masks"].to(self.device, non_blocking=self.device.type == "cuda"),
            size=self.imgsz,
            mode="bilinear",
            align_corners=False,
        )

        if self.model.non_overlap_masks_for_mem_enc:
            high_res_masks = self.model._apply_non_overlapping_constraints(high_res_masks)
        maskmem_features, maskmem_pos_enc = self.model._encode_new_memory(
            current_vision_feats=self.vision_feats,
            feat_sizes=self.feat_sizes,
            pred_masks_high_res=high_res_masks,
            object_score_logits=consolidated_out["object_score_logits"],
            is_mask_from_pts=True,
        )
        consolidated_out["maskmem_features"] = maskmem_features
        consolidated_out["maskmem_pos_enc"] = maskmem_pos_enc
        self.memory_bank.append(consolidated_out)