def add_eval_dict(self, eval_dict):
    """Observes an evaluation result dict for a single example.

    When executing eagerly, once all observations have been observed by this
    method you can use `.evaluate()` to get the final metrics.

    When using `tf.estimator.Estimator` for evaluation this function is used by
    `get_estimator_eval_metric_ops()` to construct the metric update op.

    Args:
      eval_dict: A dictionary that holds tensors for evaluating an object
        detection model, returned from
        eval_util.result_dict_for_single_example().

    Returns:
      None when executing eagerly, or an update_op that can be used to update
      the eval metrics in `tf.estimator.EstimatorSpec`.
    """
    def update_op(
        image_id_batched,
        groundtruth_boxes_batched,
        groundtruth_classes_batched,
        groundtruth_is_crowd_batched,
        groundtruth_area_batched,
        groundtruth_keypoints_batched,
        groundtruth_keypoint_visibilities_batched,
        num_gt_boxes_per_image,
        detection_boxes_batched,
        detection_scores_batched,
        detection_classes_batched,
        detection_keypoints_batched,
        num_det_boxes_per_image,
        is_annotated_batched):
      """Update operation for adding batch of images to Coco evaluator."""

      for (image_id, gt_box, gt_class, gt_is_crowd, gt_area, gt_keyp,
           gt_keyp_vis, num_gt_box, det_box, det_score, det_class, det_keyp,
           num_det_box, is_annotated) in zip(
               image_id_batched, groundtruth_boxes_batched,
               groundtruth_classes_batched, groundtruth_is_crowd_batched,
               groundtruth_area_batched, groundtruth_keypoints_batched,
               groundtruth_keypoint_visibilities_batched,
               num_gt_boxes_per_image, detection_boxes_batched,
               detection_scores_batched, detection_classes_batched,
               detection_keypoints_batched, num_det_boxes_per_image,
               is_annotated_batched):
        if is_annotated:
          self.add_single_ground_truth_image_info(
              image_id, {
                  'groundtruth_boxes': gt_box[:num_gt_box],
                  'groundtruth_classes': gt_class[:num_gt_box],
                  'groundtruth_is_crowd': gt_is_crowd[:num_gt_box],
                  'groundtruth_area': gt_area[:num_gt_box],
                  'groundtruth_keypoints': gt_keyp[:num_gt_box],
                  'groundtruth_keypoint_visibilities': gt_keyp_vis[:num_gt_box]
              })
          self.add_single_detected_image_info(
              image_id, {
                  'detection_boxes': det_box[:num_det_box],
                  'detection_scores': det_score[:num_det_box],
                  'detection_classes': det_class[:num_det_box],
                  'detection_keypoints': det_keyp[:num_det_box],
              })

    # Unpack items from the evaluation dictionary.
    input_data_fields = standard_fields.InputDataFields
    detection_fields = standard_fields.DetectionResultFields
    image_id = eval_dict[input_data_fields.key]
    groundtruth_boxes = eval_dict[input_data_fields.groundtruth_boxes]
    groundtruth_classes = eval_dict[input_data_fields.groundtruth_classes]
    groundtruth_is_crowd = eval_dict.get(input_data_fields.groundtruth_is_crowd,
                                         None)
    groundtruth_area = eval_dict.get(input_data_fields.groundtruth_area, None)
    groundtruth_keypoints = eval_dict[input_data_fields.groundtruth_keypoints]
    groundtruth_keypoint_visibilities = eval_dict.get(
        input_data_fields.groundtruth_keypoint_visibilities, None)
    detection_boxes = eval_dict[detection_fields.detection_boxes]
    detection_scores = eval_dict[detection_fields.detection_scores]
    detection_classes = eval_dict[detection_fields.detection_classes]
    detection_keypoints = eval_dict[detection_fields.detection_keypoints]
    num_gt_boxes_per_image = eval_dict.get(
        'num_groundtruth_boxes_per_image', None)
    num_det_boxes_per_image = eval_dict.get('num_det_boxes_per_image', None)
    is_annotated = eval_dict.get('is_annotated', None)

    if groundtruth_is_crowd is None:
      groundtruth_is_crowd = tf.zeros_like(groundtruth_classes, dtype=tf.bool)

    if groundtruth_area is None:
      groundtruth_area = tf.zeros_like(groundtruth_classes, dtype=tf.float32)

    if not image_id.shape.as_list():
      # Apply a batch dimension to all tensors.
      image_id = tf.expand_dims(image_id, 0)
      groundtruth_boxes = tf.expand_dims(groundtruth_boxes, 0)
      groundtruth_classes = tf.expand_dims(groundtruth_classes, 0)
      groundtruth_is_crowd = tf.expand_dims(groundtruth_is_crowd, 0)
      groundtruth_area = tf.expand_dims(groundtruth_area, 0)
      groundtruth_keypoints = tf.expand_dims(groundtruth_keypoints, 0)
      detection_boxes = tf.expand_dims(detection_boxes, 0)
      detection_scores = tf.expand_dims(detection_scores, 0)
      detection_classes = tf.expand_dims(detection_classes, 0)
      detection_keypoints = tf.expand_dims(detection_keypoints, 0)

      if num_gt_boxes_per_image is None:
        num_gt_boxes_per_image = tf.shape(groundtruth_boxes)[1:2]
      else:
        num_gt_boxes_per_image = tf.expand_dims(num_gt_boxes_per_image, 0)

      if num_det_boxes_per_image is None:
        num_det_boxes_per_image = tf.shape(detection_boxes)[1:2]
      else:
        num_det_boxes_per_image = tf.expand_dims(num_det_boxes_per_image, 0)

      if is_annotated is None:
        is_annotated = tf.constant([True])
      else:
        is_annotated = tf.expand_dims(is_annotated, 0)

      if groundtruth_keypoint_visibilities is None:
        groundtruth_keypoint_visibilities = tf.fill([
            tf.shape(groundtruth_boxes)[1],
            tf.shape(groundtruth_keypoints)[2]
        ], tf.constant(2, dtype=tf.int32))
      groundtruth_keypoint_visibilities = tf.expand_dims(
          groundtruth_keypoint_visibilities, 0)
    else:
      if num_gt_boxes_per_image is None:
        num_gt_boxes_per_image = tf.tile(
            tf.shape(groundtruth_boxes)[1:2],
            multiples=tf.shape(groundtruth_boxes)[0:1])
      if num_det_boxes_per_image is None:
        num_det_boxes_per_image = tf.tile(
            tf.shape(detection_boxes)[1:2],
            multiples=tf.shape(detection_boxes)[0:1])
      if is_annotated is None:
        is_annotated = tf.ones_like(image_id, dtype=tf.bool)
      if groundtruth_keypoint_visibilities is None:
        groundtruth_keypoint_visibilities = tf.fill([
            tf.shape(groundtruth_keypoints)[1],
            tf.shape(groundtruth_keypoints)[2]
        ], tf.constant(2, dtype=tf.int32))
        groundtruth_keypoint_visibilities = tf.tile(
            tf.expand_dims(groundtruth_keypoint_visibilities, 0),
            multiples=[tf.shape(groundtruth_keypoints)[0], 1, 1])

    return tf.py_func(update_op, [
        image_id, groundtruth_boxes, groundtruth_classes, groundtruth_is_crowd,
        groundtruth_area, groundtruth_keypoints,
        groundtruth_keypoint_visibilities, num_gt_boxes_per_image,
        detection_boxes, detection_scores, detection_classes,
        detection_keypoints, num_det_boxes_per_image, is_annotated
    ], [])