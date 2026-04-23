def _generate_detections_v1(
    boxes: tf.Tensor,
    scores: tf.Tensor,
    attributes: Optional[Mapping[str, tf.Tensor]] = None,
    pre_nms_top_k: int = 5000,
    pre_nms_score_threshold: float = 0.05,
    nms_iou_threshold: float = 0.5,
    max_num_detections: int = 100,
    soft_nms_sigma: Optional[float] = None,
):
  """Generates the final detections given the model outputs.

  The implementation unrolls the batch dimension and process images one by one.
  It required the batch dimension to be statically known and it is TPU
  compatible.

  Args:
    boxes: A `tf.Tensor` with shape `[batch_size, N, num_classes, 4]` or
      `[batch_size, N, 1, 4]` for box predictions on all feature levels. The N
      is the number of total anchors on all levels.
    scores: A `tf.Tensor` with shape `[batch_size, N, num_classes]`, which
      stacks class probability on all feature levels. The N is the number of
      total anchors on all levels. The num_classes is the number of classes
      predicted by the model. Note that the class_outputs here is the raw score.
    attributes: None or a dict of (attribute_name, attributes) pairs. Each
      attributes is a `tf.Tensor` with shape `[batch_size, N, num_classes,
      attribute_size]` or `[batch_size, N, 1, attribute_size]` for attribute
      predictions on all feature levels. The N is the number of total anchors on
      all levels. Can be None if no attribute learning is required.
    pre_nms_top_k: An `int` number of top candidate detections per class before
      NMS.
    pre_nms_score_threshold: A `float` representing the threshold for deciding
      when to remove boxes based on score.
    nms_iou_threshold: A `float` representing the threshold for deciding whether
      boxes overlap too much with respect to IOU.
    max_num_detections: A scalar representing maximum number of boxes retained
      over all classes.
    soft_nms_sigma: A `float` representing the sigma parameter for Soft NMS.
      When soft_nms_sigma=0.0 (which is default), we fall back to standard NMS.

  Returns:
    nms_boxes: A `float` type `tf.Tensor` of shape
      `[batch_size, max_num_detections, 4]` representing top detected boxes in
      `[y1, x1, y2, x2]`.
    nms_scores: A `float` type `tf.Tensor` of shape
      `[batch_size, max_num_detections]` representing sorted confidence scores
      for detected boxes. The values are between `[0, 1]`.
    nms_classes: An `int` type `tf.Tensor` of shape
      `[batch_size, max_num_detections]` representing classes for detected
      boxes.
    valid_detections: An `int` type `tf.Tensor` of shape `[batch_size]` only the
       top `valid_detections` boxes are valid detections.
    nms_attributes: None or a dict of (attribute_name, attributes). Each
      attribute is a `float` type `tf.Tensor` of shape
      `[batch_size, max_num_detections, attribute_size]` representing attribute
      predictions for detected boxes. Can be an empty dict if no attribute
      learning is required.
  """
  with tf.name_scope('generate_detections'):
    batch_size = scores.get_shape().as_list()[0]
    nmsed_boxes = []
    nmsed_classes = []
    nmsed_scores = []
    valid_detections = []
    if attributes:
      nmsed_attributes = {att_name: [] for att_name in attributes.keys()}
    else:
      nmsed_attributes = {}

    for i in range(batch_size):
      (
          nmsed_boxes_i,
          nmsed_scores_i,
          nmsed_classes_i,
          valid_detections_i,
          nmsed_att_i,
      ) = _generate_detections_per_image(
          boxes[i],
          scores[i],
          attributes={att_name: att[i] for att_name, att in attributes.items()}
          if attributes
          else {},
          pre_nms_top_k=pre_nms_top_k,
          pre_nms_score_threshold=pre_nms_score_threshold,
          nms_iou_threshold=nms_iou_threshold,
          max_num_detections=max_num_detections,
          soft_nms_sigma=soft_nms_sigma,
      )
      nmsed_boxes.append(nmsed_boxes_i)
      nmsed_scores.append(nmsed_scores_i)
      nmsed_classes.append(nmsed_classes_i)
      valid_detections.append(valid_detections_i)
      if attributes:
        for att_name in attributes.keys():
          nmsed_attributes[att_name].append(nmsed_att_i[att_name])

  nmsed_boxes = tf.stack(nmsed_boxes, axis=0)
  nmsed_scores = tf.stack(nmsed_scores, axis=0)
  nmsed_classes = tf.stack(nmsed_classes, axis=0)
  valid_detections = tf.stack(valid_detections, axis=0)
  if attributes:
    for att_name in attributes.keys():
      nmsed_attributes[att_name] = tf.stack(nmsed_attributes[att_name], axis=0)

  return (
      nmsed_boxes,
      nmsed_scores,
      nmsed_classes,
      valid_detections,
      nmsed_attributes,
  )