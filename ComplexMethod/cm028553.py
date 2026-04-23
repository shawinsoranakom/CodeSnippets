def _format_ava_eval_data(
      self, scores, boxes, groundtruth_classes, groundtruth_boxes):
    """Converts data in the correct evaluation format.

    Args:
      scores: float32 numpy array of shape [N, C] for prediction scores.
      boxes: float32 numpy array of shape [N, 4] for prediction boxes.
      groundtruth_classes: float32 numpy array of shape [N] indicates 0-index
        groundtruth classes.
      groundtruth_boxes: float32 numpy array of shape [N, 4] of corresponding
        groundtruth boxes.

    Returns:
      output_dict: the dictionary contains formatted numpy arrays.
    """
    instances_mask = np.sum(boxes, axis=-1) > 0
    scores = scores[instances_mask]
    boxes = boxes[instances_mask]

    groundtruth_mask = np.sum(groundtruth_boxes, axis=-1) > 0
    valid_gt_classes = groundtruth_classes[groundtruth_mask]
    valid_gt_boxes = groundtruth_boxes[groundtruth_mask]

    # There are circumstances that no groundtruth is provided for current clip.
    if valid_gt_classes.size == 0:
      return None

    formatted_groundtruth_boxes = []
    formatted_groundtruth_classes = []
    formatted_detection_boxes = []
    formatted_detection_classes = []
    formatted_detection_scores = []
    for i in range(valid_gt_boxes.shape[0]):
      # Only evaluate AVA 60-classes.
      if (valid_gt_classes[i] + 1) not in _AVA_LABELS_60:
        continue
      formatted_groundtruth_boxes.append(valid_gt_boxes[i] * _IMAGE_SIZE)
      formatted_groundtruth_classes.append(valid_gt_classes[i] + 1)

    for i in range(scores.shape[0]):
      one_scores = scores[i].tolist()
      for cls_idx, score in enumerate(one_scores):
        # Only evaluate AVA 60-classes.
        if (cls_idx + 1) not in _AVA_LABELS_60:
          continue
        formatted_detection_boxes.append(boxes[i] * _IMAGE_SIZE)
        formatted_detection_classes.append(cls_idx + 1)
        formatted_detection_scores.append(score)

    if not formatted_groundtruth_boxes or not formatted_detection_boxes:
      return None
    else:
      output_dict = {
          'groundtruth_boxes': formatted_groundtruth_boxes,
          'groundtruth_classes': formatted_groundtruth_classes,
          'detection_boxes': formatted_detection_boxes,
          'detection_classes': formatted_detection_classes,
          'detection_scores': formatted_detection_scores,
      }
      return output_dict