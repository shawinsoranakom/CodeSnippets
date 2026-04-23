def _evaluate_all_masks(self):
    """Evaluate all masks and compute sum iou/TP/FP/FN."""

    sum_num_tp = {category['id']: 0 for category in self._categories}
    sum_num_fp = sum_num_tp.copy()
    sum_num_fn = sum_num_tp.copy()
    sum_tp_iou = sum_num_tp.copy()

    for image_id in self._groundtruth_class_labels:
      # Separate normal and is_crowd groundtruth
      crowd_gt_indices = self._groundtruth_is_crowd.get(image_id)
      (normal_gt_masks, normal_gt_classes, crowd_gt_masks,
       crowd_gt_classes) = self._separate_normal_and_crowd_labels(
           crowd_gt_indices, self._groundtruth_masks[image_id],
           self._groundtruth_class_labels[image_id])

      # Mask matching to normal GT.
      predicted_masks = self._predicted_masks[image_id]
      predicted_class_labels = self._predicted_class_labels[image_id]
      (overlaps, pred_matched,
       gt_matched) = self._match_predictions_to_groundtruths(
           predicted_masks,
           predicted_class_labels,
           normal_gt_masks,
           normal_gt_classes,
           self._iou_threshold,
           is_crowd=False,
           with_replacement=False)

      # Accumulate true positives.
      for (class_id, is_matched, overlap) in zip(predicted_class_labels,
                                                 pred_matched, overlaps):
        if is_matched:
          sum_num_tp[class_id] += 1
          sum_tp_iou[class_id] += overlap

      # Accumulate false negatives.
      for (class_id, is_matched) in zip(normal_gt_classes, gt_matched):
        if not is_matched:
          sum_num_fn[class_id] += 1

      # Match remaining predictions to crowd gt.
      remained_pred_indices = np.logical_not(pred_matched)
      remained_pred_masks = predicted_masks[remained_pred_indices, :, :]
      remained_pred_classes = predicted_class_labels[remained_pred_indices]
      _, pred_matched, _ = self._match_predictions_to_groundtruths(
          remained_pred_masks,
          remained_pred_classes,
          crowd_gt_masks,
          crowd_gt_classes,
          self._ioa_threshold,
          is_crowd=True,
          with_replacement=True)

      # Accumulate false positives
      for (class_id, is_matched) in zip(remained_pred_classes, pred_matched):
        if not is_matched:
          sum_num_fp[class_id] += 1
    return sum_tp_iou, sum_num_tp, sum_num_fp, sum_num_fn