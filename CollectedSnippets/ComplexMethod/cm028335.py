def compute_match_iou(iou, groundtruth_nongroup_of_is_difficult_list,
                          is_box):
      """Computes TP/FP for non group-of box matching.

      The function updates the following local variables:
        tp_fp_labels - if a box is matched to group-of
        is_matched_to_difficult - the detections that were processed at this are
          matched to difficult box.
        is_matched_to_box - the detections that were processed at this stage are
          marked as is_box.

      Args:
        iou: intersection-over-union matrix [num_gt_boxes]x[num_det_boxes].
        groundtruth_nongroup_of_is_difficult_list: boolean that specifies if gt
          box is difficult.
        is_box: boolean that specifies if currently boxes or masks are
          processed.
      """
      max_overlap_gt_ids = np.argmax(iou, axis=1)
      is_gt_detected = np.zeros(iou.shape[1], dtype=bool)
      for i in range(num_detected_boxes):
        gt_id = max_overlap_gt_ids[i]
        is_evaluatable = (not tp_fp_labels[i] and
                          not is_matched_to_difficult[i] and
                          iou[i, gt_id] >= self.matching_iou_threshold and
                          not is_matched_to_group_of[i])
        if is_evaluatable:
          if not groundtruth_nongroup_of_is_difficult_list[gt_id]:
            if not is_gt_detected[gt_id]:
              tp_fp_labels[i] = True
              is_gt_detected[gt_id] = True
              is_matched_to_box[i] = is_box
          else:
            is_matched_to_difficult[i] = True