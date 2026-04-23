def _process_hotstart(
        self,
        inference_session: Sam3VideoInferenceSession,
        frame_idx: int,
        reverse: bool,
        det_to_matched_trk_obj_ids: dict[int, list[int]],
        new_det_obj_ids: list[int],
        empty_trk_obj_ids: list[int],
        unmatched_trk_obj_ids: list[int],
        extra_metadata: dict[str, Any],
        streaming: bool = False,
    ):
        """
        Handle hotstart heuristics to remove unmatched or duplicated objects.

        In streaming mode, hotstart removal logic is disabled since we don't have
        future frames to make informed decisions about object removal.
        """
        # obj_id --> first frame index where the object was detected
        obj_first_frame_idx = extra_metadata["obj_first_frame_idx"]
        # obj_id --> [mismatched frame indices]
        unmatched_frame_inds = extra_metadata["unmatched_frame_inds"]
        trk_keep_alive = extra_metadata["trk_keep_alive"]
        # (first_appear_obj_id, obj_id) --> [overlap frame indices]
        overlap_pair_to_frame_inds = extra_metadata["overlap_pair_to_frame_inds"]
        # removed_obj_ids: object IDs that are suppressed via hot-start
        removed_obj_ids = extra_metadata["removed_obj_ids"]
        suppressed_obj_ids = extra_metadata["suppressed_obj_ids"][frame_idx]

        obj_ids_newly_removed = set()  # object IDs to be newly removed on this frame
        hotstart_diff = frame_idx - self.hotstart_delay if not reverse else frame_idx + self.hotstart_delay

        # Step 1: log the frame index where each object ID first appears
        for obj_id in new_det_obj_ids:
            if obj_id not in obj_first_frame_idx:
                obj_first_frame_idx[obj_id] = frame_idx
            trk_keep_alive[int(obj_id)] = self.init_trk_keep_alive

        matched_trks = set()
        # We use the det-->tracks list to check for matched objects. Otherwise, we need to compute areas to decide whether they're occluded
        for matched_trks_per_det in det_to_matched_trk_obj_ids.values():
            matched_trks.update({int(obj_id) for obj_id in matched_trks_per_det})
        for obj_id in matched_trks:
            # NOTE: To minimize number of configurable params, we use the hotstart_unmatch_thresh to set the max value of trk_keep_alive
            trk_keep_alive[int(obj_id)] = min(self.max_trk_keep_alive, trk_keep_alive[int(obj_id)] + 1)
        for obj_id in unmatched_trk_obj_ids:
            unmatched_frame_inds[obj_id].append(frame_idx)
            # NOTE: To minimize number of configurable params, we use the hotstart_unmatch_thresh to set the min value of trk_keep_alive
            # The max keep alive is 2x the min, means the model prefers to keep the prediction rather than suppress it if it was matched long enough.
            trk_keep_alive[int(obj_id)] = max(self.min_trk_keep_alive, trk_keep_alive[int(obj_id)] - 1)
        if self.decrease_trk_keep_alive_for_empty_masklets:
            for obj_id in empty_trk_obj_ids:
                # NOTE: To minimize number of configurable params, we use the hotstart_unmatch_thresh to set the min value of trk_keep_alive
                trk_keep_alive[int(obj_id)] = max(self.min_trk_keep_alive, trk_keep_alive[int(obj_id)] - 1)

        # Step 2: removed tracks that has not matched with detections for `hotstart_unmatch_thresh` frames with hotstart period
        # a) add unmatched frame indices for each existing object ID
        # note that `unmatched_trk_obj_ids` contains those frames where the SAM2 output mask
        # doesn't match any FA detection; it excludes those frames where SAM2 gives an empty mask
        # b) remove a masklet if it first appears after `hotstart_diff` and is unmatched for more
        # than `self.hotstart_unmatch_thresh` frames
        # NOTE: In streaming mode, we skip hotstart removal logic since we don't have future frames
        if not streaming:
            for obj_id, frame_indices in unmatched_frame_inds.items():
                if obj_id in removed_obj_ids or obj_id in obj_ids_newly_removed:
                    continue  # skip if the object is already removed
                if len(frame_indices) >= self.hotstart_unmatch_thresh:
                    is_within_hotstart = (obj_first_frame_idx[obj_id] > hotstart_diff and not reverse) or (
                        obj_first_frame_idx[obj_id] < hotstart_diff and reverse
                    )
                    if is_within_hotstart:
                        obj_ids_newly_removed.add(obj_id)
                        logger.info(
                            f"Removing object {obj_id} at frame {frame_idx} "
                            f"since it is unmatched for frames: {frame_indices}"
                        )
                if (
                    trk_keep_alive[obj_id] <= 0  # Object has not been matched for too long
                    and not self.suppress_unmatched_only_within_hotstart
                    and obj_id not in removed_obj_ids
                    and obj_id not in obj_ids_newly_removed
                ):
                    logger.debug(f"Suppressing object {obj_id} at frame {frame_idx}, due to being unmatched")
                    suppressed_obj_ids.add(obj_id)

        # Step 3: removed tracks that overlaps with another track for `hotstart_dup_thresh` frames
        # a) find overlaps tracks -- we consider overlap if they match to the same detection
        # NOTE: In streaming mode, we still track overlaps for metadata but skip removal logic
        for matched_trk_obj_ids in det_to_matched_trk_obj_ids.values():
            if len(matched_trk_obj_ids) < 2:
                continue  # only count detections that are matched to multiple (>=2) masklets
            # if there are multiple matched track ids, we need to find the one that appeared first;
            # these later appearing ids may be removed since they may be considered as duplicates
            first_appear_obj_id = (
                min(matched_trk_obj_ids, key=lambda x: obj_first_frame_idx[x])
                if not reverse
                else max(matched_trk_obj_ids, key=lambda x: obj_first_frame_idx[x])
            )
            for obj_id in matched_trk_obj_ids:
                if obj_id != first_appear_obj_id:
                    key = (first_appear_obj_id, obj_id)
                    overlap_pair_to_frame_inds[key].append(frame_idx)

        # b) remove a masklet if it first appears after `hotstart_diff` and it overlaps with another
        # masklet (that appears earlier) for more than `self.hotstart_dup_thresh` frames
        # NOTE: In streaming mode, we skip hotstart removal logic since we don't have future frames
        if not streaming:
            for (first_obj_id, obj_id), frame_indices in overlap_pair_to_frame_inds.items():
                if obj_id in removed_obj_ids or obj_id in obj_ids_newly_removed:
                    continue  # skip if the object is already removed
                if (obj_first_frame_idx[obj_id] > hotstart_diff and not reverse) or (
                    obj_first_frame_idx[obj_id] < hotstart_diff and reverse
                ):
                    if len(frame_indices) >= self.hotstart_dup_thresh:
                        obj_ids_newly_removed.add(obj_id)
                        logger.info(
                            f"Removing object {obj_id} at frame {frame_idx} "
                            f"since it overlaps with another track {first_obj_id} at frames: {frame_indices}"
                        )

        removed_obj_ids.update(obj_ids_newly_removed)
        return obj_ids_newly_removed, extra_metadata