def run_tracker_update_planning_phase(
        self,
        inference_session: Sam3VideoInferenceSession,
        frame_idx: int,
        reverse: bool,
        det_out: dict[str, Tensor],
        tracker_low_res_masks_global: Tensor,
        tracker_obj_scores_global: Tensor,
        det_idx_to_prompt_id: dict[int, int],
        streaming: bool = False,
    ):
        # initialize new metadata from previous metadata (its values will be updated later)
        tracker_metadata_new = {
            "obj_ids": deepcopy(inference_session.obj_ids),
            "obj_id_to_score": deepcopy(inference_session.obj_id_to_score),
            "obj_id_to_tracker_score_frame_wise": deepcopy(inference_session.obj_id_to_tracker_score_frame_wise),
            "obj_id_to_last_occluded": {},  # will be filled later
            "max_obj_id": deepcopy(inference_session.max_obj_id),
        }

        # Initialize reconditioned_obj_ids early to avoid UnboundLocalError
        reconditioned_obj_ids = set()

        # Step 1: make the update plan and resolve heuristics
        det_mask_preds: Tensor = det_out["mask"]  # low-res mask logits
        det_scores: Tensor = det_out["scores"].float()  # Keep as tensor!
        # det_idx_to_prompt_id maps every detection index to its prompt_id (created by _merge_detections_from_prompts).
        det_prompt_ids = (
            torch.tensor(
                [det_idx_to_prompt_id[idx] for idx in range(det_mask_preds.size(0))],
                device=det_mask_preds.device,
                dtype=torch.long,
            )
            if det_mask_preds.size(0) > 0
            else torch.empty(0, device=det_mask_preds.device, dtype=torch.long)
        )
        # Get prompt IDs for tracked objects.
        trk_prompt_ids = (
            torch.tensor(
                [inference_session.obj_id_to_prompt_id[obj_id] for obj_id in inference_session.obj_ids],
                device=tracker_low_res_masks_global.device
                if tracker_low_res_masks_global.numel() > 0
                else det_mask_preds.device,
                dtype=torch.long,
            )
            if tracker_low_res_masks_global.numel() > 0
            else torch.empty(0, device=det_mask_preds.device, dtype=torch.long)
        )
        # a) match FA and SAM2 masks and find new objects
        (
            new_det_out_inds,
            unmatched_trk_obj_ids,
            det_to_matched_trk_obj_ids,
            trk_id_to_max_iou_high_conf_det,
            empty_trk_obj_ids,
        ) = self._associate_det_trk(
            det_masks=det_mask_preds,
            det_scores=det_scores,
            trk_masks=tracker_low_res_masks_global,
            trk_obj_ids=inference_session.obj_ids,
            det_prompt_ids=det_prompt_ids,
            trk_prompt_ids=trk_prompt_ids,
        )

        # check whether we've hit the maximum number of objects we can track (and if so, drop some detections)
        prev_obj_num = len(inference_session.obj_ids)
        new_det_num = len(new_det_out_inds)
        num_obj_dropped_due_to_limit = 0
        if prev_obj_num + new_det_num > self.max_num_objects:
            logger.warning(f"hitting {self.max_num_objects=} with {new_det_num=} and {prev_obj_num=}")
            new_det_num_to_keep = self.max_num_objects - prev_obj_num
            num_obj_dropped_due_to_limit = new_det_num - new_det_num_to_keep
            # Keep top scoring detections
            new_det_inds_tensor = torch.tensor(new_det_out_inds, dtype=torch.long, device=det_scores.device)
            scores_for_new_dets = det_scores[new_det_inds_tensor]
            _, top_inds = torch.topk(scores_for_new_dets, k=new_det_num_to_keep, largest=True)
            new_det_out_inds = [new_det_out_inds[i] for i in top_inds]
            new_det_num = len(new_det_out_inds)

        # assign object IDs to new detections
        new_det_start_obj_id = inference_session.max_obj_id + 1
        new_det_obj_ids = list(range(new_det_start_obj_id, new_det_start_obj_id + new_det_num))

        # Assign prompt IDs to new objects based on which prompt detected them.
        for obj_id, det_idx in zip(new_det_obj_ids, new_det_out_inds):
            prompt_id = det_idx_to_prompt_id[det_idx]
            inference_session.obj_id_to_prompt_id[obj_id] = prompt_id

        # b) handle hotstart heuristics to remove objects
        extra_metadata_new = deepcopy(
            {
                "obj_first_frame_idx": inference_session.obj_first_frame_idx,
                "unmatched_frame_inds": inference_session.unmatched_frame_inds,
                "trk_keep_alive": inference_session.trk_keep_alive,
                "overlap_pair_to_frame_inds": inference_session.overlap_pair_to_frame_inds,
                "removed_obj_ids": inference_session.removed_obj_ids,
                "suppressed_obj_ids": inference_session.suppressed_obj_ids,
            }
        )

        obj_ids_newly_removed, extra_metadata_new = self._process_hotstart(
            inference_session=inference_session,
            frame_idx=frame_idx,
            reverse=reverse,
            det_to_matched_trk_obj_ids=det_to_matched_trk_obj_ids,
            new_det_obj_ids=new_det_obj_ids,
            empty_trk_obj_ids=empty_trk_obj_ids,
            unmatched_trk_obj_ids=unmatched_trk_obj_ids,
            extra_metadata=extra_metadata_new,
            streaming=streaming,
        )
        tracker_metadata_new["extra_metadata"] = extra_metadata_new

        # Step 3 (optional): prepare reconditioned masks based on high-confidence detections
        reconditioned_masks = {}
        reconditioned_obj_ids = set()
        should_recondition_periodic = (
            self.recondition_every_nth_frame > 0
            and frame_idx % self.recondition_every_nth_frame == 0
            and len(trk_id_to_max_iou_high_conf_det) > 0
        )

        if should_recondition_periodic:
            reconditioned_masks, reconditioned_obj_ids = self._prepare_recondition_masks(
                inference_session=inference_session,
                frame_idx=frame_idx,
                det_out=det_out,
                trk_masks=tracker_low_res_masks_global,
                trk_id_to_max_iou_high_conf_det=trk_id_to_max_iou_high_conf_det,
                tracker_obj_scores_global=tracker_obj_scores_global,
            )

        tracker_update_plan = {
            "new_det_out_inds": new_det_out_inds,  # List[int]
            "new_det_obj_ids": new_det_obj_ids,  # List[int]
            "unmatched_trk_obj_ids": unmatched_trk_obj_ids,  # List[int]
            "det_to_matched_trk_obj_ids": det_to_matched_trk_obj_ids,  # dict
            "obj_ids_newly_removed": obj_ids_newly_removed,  # set
            "num_obj_dropped_due_to_limit": num_obj_dropped_due_to_limit,  # int
            "trk_id_to_max_iou_high_conf_det": trk_id_to_max_iou_high_conf_det,  # dict
            "reconditioned_obj_ids": reconditioned_obj_ids,  # set
        }

        # Step 4: Run SAM2 memory encoder on the current frame's prediction masks
        # This uses tracker masks for most objects, but detection masks for reconditioned objects
        batch_size = tracker_low_res_masks_global.size(0)
        if batch_size > 0:
            if self.suppress_overlapping_based_on_recent_occlusion_threshold > 0.0:
                # NOTE: tracker_low_res_masks_global is updated in-place then returned
                tracker_low_res_masks_global = self._suppress_overlapping_based_on_recent_occlusion(
                    inference_session=inference_session,
                    frame_idx=frame_idx,
                    tracker_low_res_masks_global=tracker_low_res_masks_global,
                    tracker_metadata_new=tracker_metadata_new,
                    obj_ids_newly_removed=obj_ids_newly_removed,
                    reverse=reverse,
                )

            # Unified memory encoding: uses detection masks for reconditioned objects
            self._tracker_update_memories(
                inference_session=inference_session,
                frame_idx=frame_idx,
                low_res_masks=tracker_low_res_masks_global,
                reconditioned_masks=reconditioned_masks,
            )

        # Step 5: update the SAM2 metadata based on the update plan
        updated_obj_ids = tracker_metadata_new["obj_ids"]
        if len(new_det_obj_ids) > 0:
            updated_obj_ids = updated_obj_ids + new_det_obj_ids
        if len(obj_ids_newly_removed) > 0:
            updated_obj_ids = [obj_id for obj_id in updated_obj_ids if obj_id not in obj_ids_newly_removed]
        tracker_metadata_new["obj_ids"] = updated_obj_ids

        # update object scores and the maximum object ID assigned so far
        if len(new_det_obj_ids) > 0:
            # Index tensor with list of indices and convert to list
            new_det_scores = det_scores[
                torch.tensor(new_det_out_inds, dtype=torch.long, device=det_scores.device)
            ].tolist()
            tracker_metadata_new["obj_id_to_score"].update(zip(new_det_obj_ids, new_det_scores))
            # tracker scores are not available for new objects, use det score instead.
            tracker_metadata_new["obj_id_to_tracker_score_frame_wise"][frame_idx].update(
                zip(new_det_obj_ids, new_det_scores)
            )
            tracker_metadata_new["max_obj_id"] = max(
                tracker_metadata_new["max_obj_id"],
                max(new_det_obj_ids),
            )
        # for removed objects, we set their scores to a very low value (-1e4) but still
        # keep them in "obj_id_to_score" (it's easier to handle outputs this way)
        for obj_id in obj_ids_newly_removed:
            tracker_metadata_new["obj_id_to_score"][obj_id] = -1e4
            tracker_metadata_new["obj_id_to_tracker_score_frame_wise"][frame_idx][obj_id] = -1e4
            tracker_metadata_new["obj_id_to_last_occluded"].pop(obj_id, None)

        return tracker_update_plan, tracker_metadata_new