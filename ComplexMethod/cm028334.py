def _compute_tp_fp_for_single_class(self,
                                      detected_boxes,
                                      detected_scores,
                                      groundtruth_boxes,
                                      groundtruth_is_difficult_list,
                                      groundtruth_is_group_of_list,
                                      detected_masks=None,
                                      groundtruth_masks=None):
    """Labels boxes detected with the same class from the same image as tp/fp.

    Args:
      detected_boxes: A numpy array of shape [N, 4] representing detected box
        coordinates
      detected_scores: A 1-d numpy array of length N representing classification
        score
      groundtruth_boxes: A numpy array of shape [M, 4] representing ground truth
        box coordinates
      groundtruth_is_difficult_list: A boolean numpy array of length M denoting
        whether a ground truth box is a difficult instance or not. If a
        groundtruth box is difficult, every detection matching this box is
        ignored.
      groundtruth_is_group_of_list: A boolean numpy array of length M denoting
        whether a ground truth box has group-of tag. If a groundtruth box is
        group-of box, every detection matching this box is ignored.
      detected_masks: (optional) A uint8 numpy array of shape [N, height,
        width]. If not None, the scores will be computed based on masks.
      groundtruth_masks: (optional) A uint8 numpy array of shape [M, height,
        width].

    Returns:
      Two arrays of the same size, containing all boxes that were evaluated as
      being true positives or false positives; if a box matched to a difficult
      box or to a group-of box, it is ignored.

      scores: A numpy array representing the detection scores.
      tp_fp_labels: a boolean numpy array indicating whether a detection is a
          true positive.
    """
    if detected_boxes.size == 0:
      return np.array([], dtype=float), np.array([], dtype=bool)

    mask_mode = False
    if detected_masks is not None and groundtruth_masks is not None:
      mask_mode = True

    iou = np.ndarray([0, 0])
    ioa = np.ndarray([0, 0])
    iou_mask = np.ndarray([0, 0])
    ioa_mask = np.ndarray([0, 0])
    if mask_mode:
      # For Instance Segmentation Evaluation on Open Images V5, not all boxed
      # instances have corresponding segmentation annotations. Those boxes that
      # dont have segmentation annotations are represented as empty masks in
      # groundtruth_masks nd array.
      mask_presence_indicator = (np.sum(groundtruth_masks, axis=(1, 2)) > 0)

      (iou_mask, ioa_mask, scores,
       num_detected_boxes) = self._get_overlaps_and_scores_mask_mode(
           detected_boxes=detected_boxes,
           detected_scores=detected_scores,
           detected_masks=detected_masks,
           groundtruth_boxes=groundtruth_boxes[mask_presence_indicator, :],
           groundtruth_masks=groundtruth_masks[mask_presence_indicator, :],
           groundtruth_is_group_of_list=groundtruth_is_group_of_list[
               mask_presence_indicator])
      if sum(mask_presence_indicator) < len(mask_presence_indicator):
        # Not all masks are present - some masks are empty
        (iou, ioa, _,
         num_detected_boxes) = self._get_overlaps_and_scores_box_mode(
             detected_boxes=detected_boxes,
             detected_scores=detected_scores,
             groundtruth_boxes=groundtruth_boxes[~mask_presence_indicator, :],
             groundtruth_is_group_of_list=groundtruth_is_group_of_list[
                 ~mask_presence_indicator])
      num_detected_boxes = detected_boxes.shape[0]
    else:
      mask_presence_indicator = np.zeros(
          groundtruth_is_group_of_list.shape, dtype=bool)
      (iou, ioa, scores,
       num_detected_boxes) = self._get_overlaps_and_scores_box_mode(
           detected_boxes=detected_boxes,
           detected_scores=detected_scores,
           groundtruth_boxes=groundtruth_boxes,
           groundtruth_is_group_of_list=groundtruth_is_group_of_list)

    if groundtruth_boxes.size == 0:
      return scores, np.zeros(num_detected_boxes, dtype=bool)

    tp_fp_labels = np.zeros(num_detected_boxes, dtype=bool)
    is_matched_to_box = np.zeros(num_detected_boxes, dtype=bool)
    is_matched_to_difficult = np.zeros(num_detected_boxes, dtype=bool)
    is_matched_to_group_of = np.zeros(num_detected_boxes, dtype=bool)

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

    def compute_match_ioa(ioa, is_box):
      """Computes TP/FP for group-of box matching.

      The function updates the following local variables:
        is_matched_to_group_of - if a box is matched to group-of
        is_matched_to_box - the detections that were processed at this stage are
          marked as is_box.

      Args:
        ioa: intersection-over-area matrix [num_gt_boxes]x[num_det_boxes].
        is_box: boolean that specifies if currently boxes or masks are
          processed.

      Returns:
        scores_group_of: of detections matched to group-of boxes
        [num_groupof_matched].
        tp_fp_labels_group_of: boolean array of size [num_groupof_matched], all
          values are True.
      """
      scores_group_of = np.zeros(ioa.shape[1], dtype=float)
      tp_fp_labels_group_of = self.group_of_weight * np.ones(
          ioa.shape[1], dtype=float)
      max_overlap_group_of_gt_ids = np.argmax(ioa, axis=1)
      for i in range(num_detected_boxes):
        gt_id = max_overlap_group_of_gt_ids[i]
        is_evaluatable = (not tp_fp_labels[i] and
                          not is_matched_to_difficult[i] and
                          ioa[i, gt_id] >= self.matching_iou_threshold and
                          not is_matched_to_group_of[i])
        if is_evaluatable:
          is_matched_to_group_of[i] = True
          is_matched_to_box[i] = is_box
          scores_group_of[gt_id] = max(scores_group_of[gt_id], scores[i])
      selector = np.where((scores_group_of > 0) & (tp_fp_labels_group_of > 0))
      scores_group_of = scores_group_of[selector]
      tp_fp_labels_group_of = tp_fp_labels_group_of[selector]

      return scores_group_of, tp_fp_labels_group_of

    # The evaluation is done in two stages:
    # 1. Evaluate all objects that actually have instance level masks.
    # 2. Evaluate all objects that are not already evaluated as boxes.
    if iou_mask.shape[1] > 0:
      groundtruth_is_difficult_mask_list = groundtruth_is_difficult_list[
          mask_presence_indicator]
      groundtruth_is_group_of_mask_list = groundtruth_is_group_of_list[
          mask_presence_indicator]
      compute_match_iou(
          iou_mask,
          groundtruth_is_difficult_mask_list[
              ~groundtruth_is_group_of_mask_list],
          is_box=False)

    scores_mask_group_of = np.ndarray([0], dtype=float)
    tp_fp_labels_mask_group_of = np.ndarray([0], dtype=float)
    if ioa_mask.shape[1] > 0:
      scores_mask_group_of, tp_fp_labels_mask_group_of = compute_match_ioa(
          ioa_mask, is_box=False)

    # Tp-fp evaluation for non-group of boxes (if any).
    if iou.shape[1] > 0:
      groundtruth_is_difficult_box_list = groundtruth_is_difficult_list[
          ~mask_presence_indicator]
      groundtruth_is_group_of_box_list = groundtruth_is_group_of_list[
          ~mask_presence_indicator]
      compute_match_iou(
          iou,
          groundtruth_is_difficult_box_list[~groundtruth_is_group_of_box_list],
          is_box=True)

    scores_box_group_of = np.ndarray([0], dtype=float)
    tp_fp_labels_box_group_of = np.ndarray([0], dtype=float)
    if ioa.shape[1] > 0:
      scores_box_group_of, tp_fp_labels_box_group_of = compute_match_ioa(
          ioa, is_box=True)

    if mask_mode:
      # Note: here crowds are treated as ignore regions.
      valid_entries = (~is_matched_to_difficult & ~is_matched_to_group_of
                       & ~is_matched_to_box)
      return np.concatenate(
          (scores[valid_entries], scores_mask_group_of)), np.concatenate(
              (tp_fp_labels[valid_entries].astype(float),
               tp_fp_labels_mask_group_of))
    else:
      valid_entries = (~is_matched_to_difficult & ~is_matched_to_group_of)
      return np.concatenate(
          (scores[valid_entries], scores_box_group_of)), np.concatenate(
              (tp_fp_labels[valid_entries].astype(float),
               tp_fp_labels_box_group_of))