def _generate_detections_per_image(
    boxes: tf.Tensor,
    scores: tf.Tensor,
    attributes: Optional[Mapping[str, tf.Tensor]] = None,
    pre_nms_top_k: int = 5000,
    pre_nms_score_threshold: float = 0.05,
    nms_iou_threshold: float = 0.5,
    max_num_detections: int = 100,
    soft_nms_sigma: Optional[float] = None,
):
  """Generates the final detections per image given the model outputs.

  Args:
    boxes: A  `tf.Tensor` with shape `[N, num_classes, 4]` or `[N, 1, 4]`, which
      box predictions on all feature levels. The N is the number of total
      anchors on all levels.
    scores: A `tf.Tensor` with shape `[N, num_classes]`, which stacks class
      probability on all feature levels. The N is the number of total anchors on
      all levels. The num_classes is the number of classes predicted by the
      model. Note that the class_outputs here is the raw score.
    attributes: If not None, a dict of `tf.Tensor`. Each value is in shape `[N,
      num_classes, attribute_size]` or `[N, 1, attribute_size]` of attribute
      predictions on all feature levels. The N is the number of total anchors on
      all levels.
    pre_nms_top_k: An `int` number of top candidate detections per class before
      NMS.
    pre_nms_score_threshold: A `float` representing the threshold for deciding
      when to remove boxes based on score.
    nms_iou_threshold: A `float` representing the threshold for deciding whether
      boxes overlap too much with respect to IOU.
    max_num_detections: A `scalar` representing maximum number of boxes retained
      over all classes.
    soft_nms_sigma: A `float` representing the sigma parameter for Soft NMS.
      When soft_nms_sigma=0.0, we fall back to standard NMS. If set to None,
      `tf.image.non_max_suppression_padded` is called instead.

  Returns:
    nms_boxes: A `float` tf.Tensor of shape `[max_num_detections, 4]`
      representing top detected boxes in `[y1, x1, y2, x2]`.
    nms_scores: A `float` tf.Tensor of shape `[max_num_detections]` representing
      sorted confidence scores for detected boxes. The values are between [0,
      1].
    nms_classes: An `int` tf.Tensor of shape `[max_num_detections]` representing
      classes for detected boxes.
    valid_detections: An `int` tf.Tensor of shape [1] only the top
      `valid_detections` boxes are valid detections.
    nms_attributes: None or a dict. Each value is a `float` tf.Tensor of shape
      `[max_num_detections, attribute_size]` representing attribute predictions
      for detected boxes. Can be an empty dict if `attributes` is None.
  """
  nmsed_boxes = []
  nmsed_scores = []
  nmsed_classes = []
  num_classes_for_box = boxes.get_shape().as_list()[1]
  num_classes = scores.get_shape().as_list()[1]
  if attributes:
    nmsed_attributes = {att_name: [] for att_name in attributes.keys()}
  else:
    nmsed_attributes = {}

  for i in range(num_classes):
    boxes_i = boxes[:, min(num_classes_for_box - 1, i)]
    scores_i = scores[:, i]
    # Obtains pre_nms_top_k before running NMS.
    scores_i, indices = tf.nn.top_k(
        scores_i, k=tf.minimum(tf.shape(scores_i)[-1], pre_nms_top_k)
    )
    boxes_i = tf.gather(boxes_i, indices)

    if soft_nms_sigma is not None:
      (nmsed_indices_i, nmsed_scores_i) = (
          tf.image.non_max_suppression_with_scores(
              tf.cast(boxes_i, tf.float32),
              tf.cast(scores_i, tf.float32),
              max_num_detections,
              iou_threshold=nms_iou_threshold,
              score_threshold=pre_nms_score_threshold,
              soft_nms_sigma=soft_nms_sigma,
              name='nms_detections_' + str(i),
          )
      )
      nmsed_boxes_i = tf.gather(boxes_i, nmsed_indices_i)
      nmsed_boxes_i = preprocess_ops.clip_or_pad_to_fixed_size(
          nmsed_boxes_i, max_num_detections, 0.0
      )
      nmsed_scores_i = preprocess_ops.clip_or_pad_to_fixed_size(
          nmsed_scores_i, max_num_detections, -1.0
      )
    else:
      (nmsed_indices_i, nmsed_num_valid_i) = (
          tf.image.non_max_suppression_padded(
              tf.cast(boxes_i, tf.float32),
              tf.cast(scores_i, tf.float32),
              max_num_detections,
              iou_threshold=nms_iou_threshold,
              score_threshold=pre_nms_score_threshold,
              pad_to_max_output_size=True,
              name='nms_detections_' + str(i),
          )
      )
      nmsed_boxes_i = tf.gather(boxes_i, nmsed_indices_i)
      nmsed_scores_i = tf.gather(scores_i, nmsed_indices_i)
      # Sets scores of invalid boxes to -1.
      nmsed_scores_i = tf.where(
          tf.less(tf.range(max_num_detections), [nmsed_num_valid_i]),
          nmsed_scores_i,
          -tf.ones_like(nmsed_scores_i),
      )

    nmsed_classes_i = tf.fill([max_num_detections], i)
    nmsed_boxes.append(nmsed_boxes_i)
    nmsed_scores.append(nmsed_scores_i)
    nmsed_classes.append(nmsed_classes_i)
    if attributes:
      for att_name, att in attributes.items():
        num_classes_for_attr = att.get_shape().as_list()[1]
        att_i = att[:, min(num_classes_for_attr - 1, i)]
        att_i = tf.gather(att_i, indices)
        nmsed_att_i = tf.gather(att_i, nmsed_indices_i)
        nmsed_att_i = preprocess_ops.clip_or_pad_to_fixed_size(
            nmsed_att_i, max_num_detections, 0.0
        )
        nmsed_attributes[att_name].append(nmsed_att_i)

  # Concats results from all classes and sort them.
  nmsed_boxes = tf.concat(nmsed_boxes, axis=0)
  nmsed_scores = tf.concat(nmsed_scores, axis=0)
  nmsed_classes = tf.concat(nmsed_classes, axis=0)
  nmsed_scores, indices = tf.nn.top_k(
      nmsed_scores, k=max_num_detections, sorted=True
  )
  nmsed_boxes = tf.gather(nmsed_boxes, indices)
  nmsed_classes = tf.gather(nmsed_classes, indices)
  valid_detections = tf.reduce_sum(
      tf.cast(tf.greater(nmsed_scores, -1), tf.int32)
  )
  if attributes:
    for att_name in attributes.keys():
      nmsed_attributes[att_name] = tf.concat(nmsed_attributes[att_name], axis=0)
      nmsed_attributes[att_name] = tf.gather(
          nmsed_attributes[att_name], indices
      )

  return (
      nmsed_boxes,
      nmsed_scores,
      nmsed_classes,
      valid_detections,
      nmsed_attributes,
  )