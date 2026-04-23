def add_single_detected_image_info(self,
                                     image_id,
                                     detections_dict):
    """Adds detections for a single image to be used for evaluation.

    If a detection has already been added for this image id, a warning is
    logged, and the detection is skipped.

    Args:
      image_id: A unique string/integer identifier for the image.
      detections_dict: A dictionary containing -
        DetectionResultFields.detection_boxes: float32 numpy array of shape
          [num_boxes, 4] containing `num_boxes` detection boxes of the format
          [ymin, xmin, ymax, xmax] in absolute image coordinates.
        DetectionResultFields.detection_scores: float32 numpy array of shape
          [num_boxes] containing detection scores for the boxes.
        DetectionResultFields.detection_classes: integer numpy array of shape
          [num_boxes] containing 1-indexed detection classes for the boxes.
        DetectionResultFields.detection_keypoints (optional): float numpy array
          of keypoints with shape [num_boxes, num_keypoints, 2].
    Raises:
      ValueError: If groundtruth for the image_id is not available.
    """
    if image_id not in self._image_ids:
      raise ValueError('Missing groundtruth for image id: {}'.format(image_id))

    if self._image_ids[image_id]:
      tf.logging.warning('Ignoring detection with image id %s since it was '
                         'previously added', image_id)
      return

    # Drop optional fields if empty tensor.
    detection_keypoints = detections_dict.get(
        standard_fields.DetectionResultFields.detection_keypoints)
    if detection_keypoints is not None and not detection_keypoints.shape[0]:
      detection_keypoints = None

    if self._skip_predictions_for_unlabeled_class:
      det_classes = detections_dict[
          standard_fields.DetectionResultFields.detection_classes]
      num_det_boxes = det_classes.shape[0]
      keep_box_ids = []
      for box_id in range(num_det_boxes):
        if det_classes[box_id] in self._groundtruth_labeled_classes[image_id]:
          keep_box_ids.append(box_id)
      self._detection_boxes_list.extend(
          coco_tools.ExportSingleImageDetectionBoxesToCoco(
              image_id=image_id,
              category_id_set=self._category_id_set,
              detection_boxes=detections_dict[
                  standard_fields.DetectionResultFields.detection_boxes]
              [keep_box_ids],
              detection_scores=detections_dict[
                  standard_fields.DetectionResultFields.detection_scores]
              [keep_box_ids],
              detection_classes=detections_dict[
                  standard_fields.DetectionResultFields.detection_classes]
              [keep_box_ids],
              detection_keypoints=detection_keypoints))
    else:
      self._detection_boxes_list.extend(
          coco_tools.ExportSingleImageDetectionBoxesToCoco(
              image_id=image_id,
              category_id_set=self._category_id_set,
              detection_boxes=detections_dict[
                  standard_fields.DetectionResultFields.detection_boxes],
              detection_scores=detections_dict[
                  standard_fields.DetectionResultFields.detection_scores],
              detection_classes=detections_dict[
                  standard_fields.DetectionResultFields.detection_classes],
              detection_keypoints=detection_keypoints))
    self._image_ids[image_id] = True