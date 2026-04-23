def _match_predictions_to_groundtruths(self,
                                         predicted_masks,
                                         predicted_classes,
                                         groundtruth_masks,
                                         groundtruth_classes,
                                         matching_threshold,
                                         is_crowd=False,
                                         with_replacement=False):
    """Match the predicted masks to groundtruths.

    Args:
      predicted_masks: array of shape [num_predictions, height, width].
      predicted_classes: array of shape [num_predictions].
      groundtruth_masks: array of shape [num_groundtruths, height, width].
      groundtruth_classes: array of shape [num_groundtruths].
      matching_threshold: if the overlap between a prediction and a groundtruth
        is larger than this threshold, the prediction is true positive.
      is_crowd: whether the groundtruths are crowd annotation or not. If True,
        use intersection over area (IoA) as the overlapping metric; otherwise
        use intersection over union (IoU).
      with_replacement: whether a groundtruth can be matched to multiple
        predictions. By default, for normal groundtruths, only 1-1 matching is
        allowed for normal groundtruths; for crowd groundtruths, 1-to-many must
        be allowed.

    Returns:
      best_overlaps: array of shape [num_predictions]. Values representing the
      IoU
        or IoA with best matched groundtruth.
      pred_matched: array of shape [num_predictions]. Boolean value representing
        whether the ith prediction is matched to a groundtruth.
      gt_matched: array of shape [num_groundtruth]. Boolean value representing
        whether the ith groundtruth is matched to a prediction.
    Raises:
      ValueError: if the shape of groundtruth/predicted masks doesn't match
        groundtruth/predicted classes.
    """
    if groundtruth_masks.shape[0] != groundtruth_classes.shape[0]:
      raise ValueError(
          "The number of GT masks doesn't match the number of labels.")
    if predicted_masks.shape[0] != predicted_classes.shape[0]:
      raise ValueError(
          "The number of predicted masks doesn't match the number of labels.")
    gt_matched = np.zeros(groundtruth_classes.shape, dtype=bool)
    pred_matched = np.zeros(predicted_classes.shape, dtype=bool)
    best_overlaps = np.zeros(predicted_classes.shape)
    for pid in range(predicted_classes.shape[0]):
      best_overlap = 0
      matched_gt_id = -1
      for gid in range(groundtruth_classes.shape[0]):
        if predicted_classes[pid] == groundtruth_classes[gid]:
          if (not with_replacement) and gt_matched[gid]:
            continue
          if not is_crowd:
            overlap = np_mask_ops.iou(predicted_masks[pid:pid + 1],
                                      groundtruth_masks[gid:gid + 1])[0, 0]
          else:
            overlap = np_mask_ops.ioa(groundtruth_masks[gid:gid + 1],
                                      predicted_masks[pid:pid + 1])[0, 0]
          if overlap >= matching_threshold and overlap > best_overlap:
            matched_gt_id = gid
            best_overlap = overlap
      if matched_gt_id >= 0:
        gt_matched[matched_gt_id] = True
        pred_matched[pid] = True
        best_overlaps[pid] = best_overlap
    return best_overlaps, pred_matched, gt_matched