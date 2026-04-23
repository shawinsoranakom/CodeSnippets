def __call__(
      self,
      raw_boxes: tf.Tensor,
      raw_scores: tf.Tensor,
      anchor_boxes: tf.Tensor,
      image_shape: tf.Tensor,
      regression_weights: Optional[List[float]] = None,
      bbox_per_class: bool = True,
  ):
    """Generates final detections.

    Args:
      raw_boxes: A `tf.Tensor` of shape of `[batch_size, K, num_classes * 4]`
        representing the class-specific box coordinates relative to anchors.
      raw_scores: A `tf.Tensor` of shape of `[batch_size, K, num_classes]`
        representing the class logits before applying score activiation.
      anchor_boxes: A `tf.Tensor` of shape of `[batch_size, K, 4]` representing
        the corresponding anchor boxes w.r.t `box_outputs`.
      image_shape: A `tf.Tensor` of shape of `[batch_size, 2]` storing the image
        height and width w.r.t. the scaled image, i.e. the same image space as
        `box_outputs` and `anchor_boxes`.
      regression_weights: A list of four float numbers to scale coordinates.
      bbox_per_class: A `bool`. If True, perform per-class box regression.

    Returns:
      If `apply_nms` = True, the return is a dictionary with keys:
        `detection_boxes`: A `float` tf.Tensor of shape
          [batch, max_num_detections, 4] representing top detected boxes in
          [y1, x1, y2, x2].
        `detection_scores`: A `float` `tf.Tensor` of shape
          [batch, max_num_detections] representing sorted confidence scores for
          detected boxes. The values are between [0, 1].
        `detection_classes`: An `int` tf.Tensor of shape
          [batch, max_num_detections] representing classes for detected boxes.
        `num_detections`: An `int` tf.Tensor of shape [batch] only the first
          `num_detections` boxes are valid detections
      If `apply_nms` = False, the return is a dictionary with keys:
        `decoded_boxes`: A `float` tf.Tensor of shape [batch, num_raw_boxes, 4]
          representing all the decoded boxes.
        `decoded_box_scores`: A `float` tf.Tensor of shape
          [batch, num_raw_boxes] representing socres of all the decoded boxes.
    """
    if self._config_dict['use_sigmoid_probability']:
      box_scores = tf.math.sigmoid(raw_scores)
    else:
      box_scores = tf.nn.softmax(raw_scores, axis=-1)

    # Removes the background class.
    box_scores_shape = tf.shape(box_scores)
    box_scores_shape_list = box_scores.get_shape().as_list()
    batch_size = box_scores_shape[0]
    num_locations = box_scores_shape_list[1]
    num_classes = box_scores_shape_list[-1]

    box_scores = tf.slice(box_scores, [0, 0, 1], [-1, -1, -1])

    if bbox_per_class:
      num_detections = num_locations * (num_classes - 1)
      raw_boxes = tf.reshape(
          raw_boxes, [batch_size, num_locations, num_classes, 4]
      )
      raw_boxes = tf.slice(raw_boxes, [0, 0, 1, 0], [-1, -1, -1, -1])
      anchor_boxes = tf.tile(
          tf.expand_dims(anchor_boxes, axis=2), [1, 1, num_classes - 1, 1]
      )
      raw_boxes = tf.reshape(raw_boxes, [batch_size, num_detections, 4])
      anchor_boxes = tf.reshape(anchor_boxes, [batch_size, num_detections, 4])

    # Box decoding.
    decoded_boxes = box_ops.decode_boxes(
        raw_boxes, anchor_boxes, weights=regression_weights
    )

    # Box clipping.
    if image_shape is not None:
      decoded_boxes = box_ops.clip_boxes(
          decoded_boxes, tf.expand_dims(image_shape, axis=1)
      )

    if bbox_per_class:
      decoded_boxes = tf.reshape(
          decoded_boxes, [batch_size, num_locations, num_classes - 1, 4]
      )
    else:
      decoded_boxes = tf.expand_dims(decoded_boxes, axis=2)

    if not self._config_dict['apply_nms']:
      return {
          'decoded_boxes': decoded_boxes,
          'decoded_box_scores': box_scores,
      }

    # Optionally force the NMS be run on CPU.
    if self._config_dict['use_cpu_nms']:
      nms_context = tf.device('cpu:0')
    else:
      nms_context = contextlib.nullcontext()

    with nms_context:
      if self._config_dict['nms_version'] == 'batched':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections) = (
            _generate_detections_batched(
                decoded_boxes,
                box_scores,
                self._config_dict['pre_nms_score_threshold'],
                self._config_dict['nms_iou_threshold'],
                self._config_dict['max_num_detections'],
            )
        )
      elif self._config_dict['nms_version'] == 'v1':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections, _) = (
            _generate_detections_v1(
                decoded_boxes,
                box_scores,
                pre_nms_top_k=self._config_dict['pre_nms_top_k'],
                pre_nms_score_threshold=self._config_dict[
                    'pre_nms_score_threshold'
                ],
                nms_iou_threshold=self._config_dict['nms_iou_threshold'],
                max_num_detections=self._config_dict['max_num_detections'],
                soft_nms_sigma=self._config_dict['soft_nms_sigma'],
            )
        )
      elif self._config_dict['nms_version'] == 'v2':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections) = (
            _generate_detections_v2(
                decoded_boxes,
                box_scores,
                pre_nms_top_k=self._config_dict['pre_nms_top_k'],
                pre_nms_score_threshold=self._config_dict[
                    'pre_nms_score_threshold'
                ],
                nms_iou_threshold=self._config_dict['nms_iou_threshold'],
                max_num_detections=self._config_dict['max_num_detections'],
            )
        )
      else:
        raise ValueError(
            'NMS version {} not supported.'.format(
                self._config_dict['nms_version']
            )
        )

    # Adds 1 to offset the background class which has index 0.
    nmsed_classes += 1

    return {
        'num_detections': valid_detections,
        'detection_boxes': nmsed_boxes,
        'detection_classes': nmsed_classes,
        'detection_scores': nmsed_scores,
    }