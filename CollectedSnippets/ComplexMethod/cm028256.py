def get_estimator_eval_metric_ops(self, eval_dict):
    """Returns a dictionary of eval metric ops.

    Note that once value_op is called, the detections and groundtruth added via
    update_op are cleared.

    This function can take in groundtruth and detections for a batch of images,
    or for a single image. For the latter case, the batch dimension for input
    tensors need not be present.

    Args:
      eval_dict: A dictionary that holds tensors for evaluating object detection
        performance. For single-image evaluation, this dictionary may be
        produced from eval_util.result_dict_for_single_example(). If multi-image
        evaluation, `eval_dict` should contain the fields
        'num_groundtruth_boxes_per_image' and 'num_det_boxes_per_image' to
        properly unpad the tensors from the batch.

    Returns:
      a dictionary of metric names to tuple of value_op and update_op that can
      be used as eval metric ops in tf.estimator.EstimatorSpec. Note that all
      update ops must be run together and similarly all value ops must be run
      together to guarantee correct behaviour.
    """
    # Unpack items from the evaluation dictionary.
    input_data_fields = standard_fields.InputDataFields
    detection_fields = standard_fields.DetectionResultFields
    image_id = eval_dict[input_data_fields.key]
    groundtruth_boxes = eval_dict[input_data_fields.groundtruth_boxes]
    groundtruth_classes = eval_dict[input_data_fields.groundtruth_classes]
    detection_boxes = eval_dict[detection_fields.detection_boxes]
    detection_scores = eval_dict[detection_fields.detection_scores]
    detection_classes = eval_dict[detection_fields.detection_classes]
    num_gt_boxes_per_image = eval_dict.get(
        'num_groundtruth_boxes_per_image', None)
    num_det_boxes_per_image = eval_dict.get('num_det_boxes_per_image', None)
    is_annotated_batched = eval_dict.get('is_annotated', None)

    if not image_id.shape.as_list():
      # Apply a batch dimension to all tensors.
      image_id = tf.expand_dims(image_id, 0)
      groundtruth_boxes = tf.expand_dims(groundtruth_boxes, 0)
      groundtruth_classes = tf.expand_dims(groundtruth_classes, 0)
      detection_boxes = tf.expand_dims(detection_boxes, 0)
      detection_scores = tf.expand_dims(detection_scores, 0)
      detection_classes = tf.expand_dims(detection_classes, 0)

      if num_gt_boxes_per_image is None:
        num_gt_boxes_per_image = tf.shape(groundtruth_boxes)[1:2]
      else:
        num_gt_boxes_per_image = tf.expand_dims(num_gt_boxes_per_image, 0)

      if num_det_boxes_per_image is None:
        num_det_boxes_per_image = tf.shape(detection_boxes)[1:2]
      else:
        num_det_boxes_per_image = tf.expand_dims(num_det_boxes_per_image, 0)

      if is_annotated_batched is None:
        is_annotated_batched = tf.constant([True])
      else:
        is_annotated_batched = tf.expand_dims(is_annotated_batched, 0)
    else:
      if num_gt_boxes_per_image is None:
        num_gt_boxes_per_image = tf.tile(
            tf.shape(groundtruth_boxes)[1:2],
            multiples=tf.shape(groundtruth_boxes)[0:1])
      if num_det_boxes_per_image is None:
        num_det_boxes_per_image = tf.tile(
            tf.shape(detection_boxes)[1:2],
            multiples=tf.shape(detection_boxes)[0:1])
      if is_annotated_batched is None:
        is_annotated_batched = tf.ones_like(image_id, dtype=tf.bool)

    # Filter images based on is_annotated_batched and match detections.
    image_info = [tf.boolean_mask(tensor, is_annotated_batched) for tensor in
                  [groundtruth_boxes, groundtruth_classes,
                   num_gt_boxes_per_image, detection_boxes, detection_classes,
                   num_det_boxes_per_image]]
    is_class_matched = tf.map_fn(
        self.match_single_image_info, image_info, dtype=tf.int64)
    y_true = tf.squeeze(is_class_matched)
    y_pred = tf.squeeze(tf.boolean_mask(detection_scores, is_annotated_batched))
    ece, update_op = calibration_metrics.expected_calibration_error(
        y_true, y_pred)
    return {'CalibrationError/ExpectedCalibrationError': (ece, update_op)}