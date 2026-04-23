def run_tracker_update_planning_phase(
        self,
        frame_idx: int,
        reverse: bool,
        det_out: dict[str, torch.Tensor],
        tracker_low_res_masks_global: torch.Tensor,
        tracker_obj_scores_global: torch.Tensor,
        tracker_metadata_prev: dict[str, np.ndarray],
        tracker_states_local: list[Any],
    ):
        """Run the tracker update planning phase for a single frame in an SPMD manner."""
        # initialize new metadata from previous metadata (its values will be updated later)
        tracker_metadata_new = {
            "obj_ids": deepcopy(tracker_metadata_prev["obj_ids"]),
            "num_obj": deepcopy(tracker_metadata_prev["num_obj"]),
            "obj_id_to_score": deepcopy(tracker_metadata_prev["obj_id_to_score"]),
            "obj_id_to_cls": deepcopy(tracker_metadata_prev["obj_id_to_cls"]),
            "obj_id_to_tracker_score_frame_wise": deepcopy(tracker_metadata_prev["obj_id_to_tracker_score_frame_wise"]),
            "obj_id_to_last_occluded": {},  # will be filled later
            "max_obj_id": deepcopy(tracker_metadata_prev["max_obj_id"]),
        }

        # Initialize reconditioned_obj_ids early to avoid UnboundLocalError
        reconditioned_obj_ids = set()

        # Step 1: make the update plan and resolve heuristics on GPU 0
        det_mask_preds: torch.Tensor = det_out["mask"]  # low-res mask logits
        det_scores_np: np.ndarray = det_out["scores"].float().cpu().numpy()
        det_cls_np: np.ndarray = det_out["cls"].float().cpu().numpy()
        det_bbox_xyxy: torch.Tensor = det_out["bbox"]
        # a) match detector and tracker masks and find new objects
        (
            new_det_fa_inds,
            unmatched_trk_obj_ids,
            det_to_matched_trk_obj_ids,
            trk_id_to_max_iou_high_conf_det,
            empty_trk_obj_ids,
        ) = self._associate_det_trk(
            det_masks=det_mask_preds,
            det_scores_np=det_scores_np,
            trk_masks=tracker_low_res_masks_global,
            trk_obj_ids=tracker_metadata_prev["obj_ids"],
        )
        if self.suppress_det_close_to_boundary:
            keep = self._suppress_detections_close_to_boundary(det_bbox_xyxy[new_det_fa_inds])
            new_det_fa_inds = new_det_fa_inds[keep.cpu().numpy()]

        # check whether we've hit the maximum number of objects we can track (and if so, drop some detections)
        prev_obj_num = np.sum(tracker_metadata_prev["num_obj"])
        new_det_num = len(new_det_fa_inds)
        num_obj_dropped_due_to_limit = 0
        if prev_obj_num + new_det_num > self.max_num_objects:
            LOGGER.warning(f"hitting {self.max_num_objects=} with {new_det_num=} and {prev_obj_num=}")
            new_det_num_to_keep = self.max_num_objects - prev_obj_num
            num_obj_dropped_due_to_limit = new_det_num - new_det_num_to_keep
            new_det_fa_inds = self._drop_new_det_with_obj_limit(new_det_fa_inds, det_scores_np, new_det_num_to_keep)
            assert len(new_det_fa_inds) == new_det_num_to_keep
            new_det_num = len(new_det_fa_inds)

        # assign object IDs to new detections and decide which GPU to place them
        new_det_obj_ids = tracker_metadata_prev["max_obj_id"] + 1 + np.arange(new_det_num)

        # b) handle hotstart heuristics to remove objects
        # here `metadata` contains metadata stored on (and only accessible to) GPU 0;
        # we avoid broadcasting them to other GPUs to save communication cost, assuming
        # that `metadata` is not needed by other GPUs
        metadata_new = deepcopy(tracker_metadata_prev["metadata"])
        if not hasattr(self, "_warm_up_complete") or self._warm_up_complete:
            obj_ids_newly_removed, metadata_new = self._process_hotstart(
                frame_idx=frame_idx,
                reverse=reverse,
                det_to_matched_trk_obj_ids=det_to_matched_trk_obj_ids,
                new_det_obj_ids=new_det_obj_ids,
                empty_trk_obj_ids=empty_trk_obj_ids,
                unmatched_trk_obj_ids=unmatched_trk_obj_ids,
                metadata=metadata_new,
            )
        else:
            # if warm-up is not complete, we don't remove any objects
            obj_ids_newly_removed = set()
        tracker_metadata_new["metadata"] = metadata_new

        # `tracker_update_plan` should be identical on all GPUs after broadcasting
        tracker_update_plan = {
            "new_det_fa_inds": new_det_fa_inds,  # np.ndarray
            "new_det_obj_ids": new_det_obj_ids,  # np.ndarray
            # "new_det_gpu_ids": new_det_gpu_ids,  # np.ndarray
            "unmatched_trk_obj_ids": unmatched_trk_obj_ids,  # np.ndarray
            "det_to_matched_trk_obj_ids": det_to_matched_trk_obj_ids,  # dict
            "obj_ids_newly_removed": obj_ids_newly_removed,  # set
            "num_obj_dropped_due_to_limit": num_obj_dropped_due_to_limit,  # int
            "trk_id_to_max_iou_high_conf_det": trk_id_to_max_iou_high_conf_det,  # dict
            "reconditioned_obj_ids": reconditioned_obj_ids,  # set
        }

        # Step 3 (optional): recondition masklets based on high-confidence detections before memory encoding
        # NOTE: Running this in execution phase (after memory encoding) can lead to suboptimal results
        should_recondition_iou = False

        # Evaluate tracklets for reconditioning based on bbox IoU mismatch with detections
        if self.reconstruction_bbox_iou_thresh > 0 and len(trk_id_to_max_iou_high_conf_det) > 0:
            for trk_obj_id, det_idx in trk_id_to_max_iou_high_conf_det.items():
                det_box = det_out["bbox"][det_idx]
                det_score = det_out["scores"][det_idx]

                try:
                    trk_idx = list(tracker_metadata_prev["obj_ids"]).index(trk_obj_id)
                except ValueError:
                    continue  # Skip if tracklet not found

                tracker_mask = tracker_low_res_masks_global[trk_idx]
                mask_binary = tracker_mask > 0
                mask_area = mask_binary.sum().item()

                if mask_area == 0:
                    continue  # Skip tracklets with zero mask area

                # Get bounding box from SAM2 mask and convert to normalized coordinates
                tracker_box_pixels = batched_mask_to_box(mask_binary.unsqueeze(0)).squeeze(0)
                mask_height, mask_width = tracker_mask.shape[-2:]
                tracker_box_normalized = torch.tensor(
                    [
                        tracker_box_pixels[0] / mask_width,
                        tracker_box_pixels[1] / mask_height,
                        tracker_box_pixels[2] / mask_width,
                        tracker_box_pixels[3] / mask_height,
                    ],
                    device=tracker_box_pixels.device,
                )

                # Compute IoU between detection and SAM2 tracklet bounding boxes
                det_box_batch = det_box.unsqueeze(0)
                tracker_box_batch = tracker_box_normalized.unsqueeze(0)
                iou = box_iou(det_box_batch, tracker_box_batch)[0]

                if iou < self.reconstruction_bbox_iou_thresh and det_score >= self.reconstruction_bbox_det_score:
                    should_recondition_iou = True
                    reconditioned_obj_ids.add(trk_obj_id)

        should_recondition_periodic = (
            self.recondition_every_nth_frame > 0
            and frame_idx % self.recondition_every_nth_frame == 0
            and len(trk_id_to_max_iou_high_conf_det) > 0
        )

        # Recondition if periodic or IoU condition met
        if should_recondition_periodic or should_recondition_iou:
            self._recondition_masklets(
                frame_idx,
                det_out,
                trk_id_to_max_iou_high_conf_det,
                tracker_states_local,
                tracker_metadata_prev,
                tracker_obj_scores_global,
            )

        # Step 4: Run SAM2 memory encoder on the current frame's prediction masks
        # This is done on all GPUs
        batch_size = tracker_low_res_masks_global.size(0)
        if batch_size > 0:
            if not hasattr(self, "_warm_up_complete") or self._warm_up_complete:
                if self.suppress_overlapping_based_on_recent_occlusion_threshold > 0.0:
                    # NOTE: tracker_low_res_masks_global is updated in-place then returned
                    tracker_low_res_masks_global = self._suppress_overlapping_based_on_recent_occlusion(
                        frame_idx,
                        tracker_low_res_masks_global,
                        tracker_metadata_prev,
                        tracker_metadata_new,
                        obj_ids_newly_removed,
                        reverse,
                    )

            self._tracker_update_memories(tracker_states_local, frame_idx, low_res_masks=tracker_low_res_masks_global)

        # Step 4: update the SAM2 metadata based on the update plan
        updated_obj_ids_this_gpu = tracker_metadata_new["obj_ids"]
        if len(new_det_obj_ids) > 0:
            updated_obj_ids_this_gpu = np.concatenate([updated_obj_ids_this_gpu, new_det_obj_ids])
        if len(obj_ids_newly_removed) > 0:
            is_removed = np.isin(updated_obj_ids_this_gpu, list(obj_ids_newly_removed))
            updated_obj_ids_this_gpu = updated_obj_ids_this_gpu[~is_removed]
        tracker_metadata_new["obj_ids"] = updated_obj_ids_this_gpu
        tracker_metadata_new["num_obj"] = len(updated_obj_ids_this_gpu)
        # update object scores and the maximum object ID assigned so far
        if len(new_det_obj_ids) > 0:
            tracker_metadata_new["obj_id_to_score"].update(zip(new_det_obj_ids, det_scores_np[new_det_fa_inds]))
            tracker_metadata_new["obj_id_to_cls"].update(zip(new_det_obj_ids, det_cls_np[new_det_fa_inds]))
            # tracker scores are not available for new objects, use det score instead.
            tracker_metadata_new["obj_id_to_tracker_score_frame_wise"][frame_idx].update(
                zip(new_det_obj_ids, det_scores_np[new_det_fa_inds])
            )
            tracker_metadata_new["max_obj_id"] = max(tracker_metadata_new["max_obj_id"], np.max(new_det_obj_ids))
        # for removed objects, we set their scores to a very low value (-1e4) but still
        # keep them in "obj_id_to_score" (it's easier to handle outputs this way)
        for obj_id in obj_ids_newly_removed:
            tracker_metadata_new["obj_id_to_score"][obj_id] = -1e4
            tracker_metadata_new["obj_id_to_tracker_score_frame_wise"][frame_idx][obj_id] = -1e4
            tracker_metadata_new["obj_id_to_last_occluded"].pop(obj_id, None)
        # check that "metadata" is in tracker_metadata_new if and only if it's GPU 0
        assert "metadata" in tracker_metadata_new
        if self.masklet_confirmation_enable:
            metadata = self.update_masklet_confirmation_status(
                metadata=tracker_metadata_new["metadata"],
                obj_ids_all_gpu_prev=tracker_metadata_prev["obj_ids"],
                obj_ids_all_gpu_updated=tracker_metadata_new["obj_ids"],
                det_to_matched_trk_obj_ids=det_to_matched_trk_obj_ids,
                new_det_obj_ids=new_det_obj_ids,
            )
            tracker_metadata_new["metadata"] = metadata

        return tracker_update_plan, tracker_metadata_new