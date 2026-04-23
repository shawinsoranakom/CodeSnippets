def add_single_detected_image_info(self,
                                     image_key,
                                     detected_boxes,
                                     detected_scores,
                                     detected_class_labels,
                                     detected_masks=None):
    """Adds detections for a single image to be used for evaluation.

    Args:
      image_key: A unique string/integer identifier for the image.
      detected_boxes: float32 numpy array of shape [num_boxes, 4] containing
        `num_boxes` detection boxes of the format [ymin, xmin, ymax, xmax] in
        absolute image coordinates.
      detected_scores: float32 numpy array of shape [num_boxes] containing
        detection scores for the boxes.
      detected_class_labels: integer numpy array of shape [num_boxes] containing
        0-indexed detection classes for the boxes.
      detected_masks: np.uint8 numpy array of shape [num_boxes, height, width]
        containing `num_boxes` detection masks with values ranging between 0 and
        1.

    Raises:
      ValueError: if the number of boxes, scores and class labels differ in
        length.
    """
    if (len(detected_boxes) != len(detected_scores) or
        len(detected_boxes) != len(detected_class_labels)):
      raise ValueError(
          'detected_boxes, detected_scores and '
          'detected_class_labels should all have same lengths. Got'
          '[%d, %d, %d]' % len(detected_boxes), len(detected_scores),
          len(detected_class_labels))

    if image_key in self.detection_keys:
      logging.warning(
          'image %s has already been added to the detection result database',
          image_key)
      return

    self.detection_keys.add(image_key)
    if image_key in self.groundtruth_boxes:
      groundtruth_boxes = self.groundtruth_boxes[image_key]
      groundtruth_class_labels = self.groundtruth_class_labels[image_key]
      # Masks are popped instead of look up. The reason is that we do not want
      # to keep all masks in memory which can cause memory overflow.
      groundtruth_masks = self.groundtruth_masks.pop(image_key)
      groundtruth_is_difficult_list = self.groundtruth_is_difficult_list[
          image_key]
      groundtruth_is_group_of_list = self.groundtruth_is_group_of_list[
          image_key]
    else:
      groundtruth_boxes = np.empty(shape=[0, 4], dtype=float)
      groundtruth_class_labels = np.array([], dtype=int)
      if detected_masks is None:
        groundtruth_masks = None
      else:
        groundtruth_masks = np.empty(shape=[0, 1, 1], dtype=float)
      groundtruth_is_difficult_list = np.array([], dtype=bool)
      groundtruth_is_group_of_list = np.array([], dtype=bool)
    scores, tp_fp_labels, is_class_correctly_detected_in_image = (
        self.per_image_eval.compute_object_detection_metrics(
            detected_boxes=detected_boxes,
            detected_scores=detected_scores,
            detected_class_labels=detected_class_labels,
            groundtruth_boxes=groundtruth_boxes,
            groundtruth_class_labels=groundtruth_class_labels,
            groundtruth_is_difficult_list=groundtruth_is_difficult_list,
            groundtruth_is_group_of_list=groundtruth_is_group_of_list,
            detected_masks=detected_masks,
            groundtruth_masks=groundtruth_masks))
    for i in range(self.num_class):
      if scores[i].shape[0] > 0:
        self.scores_per_class[i].append(scores[i])
        self.tp_fp_labels_per_class[i].append(tp_fp_labels[i])
    (self.num_images_correctly_detected_per_class
    ) += is_class_correctly_detected_in_image