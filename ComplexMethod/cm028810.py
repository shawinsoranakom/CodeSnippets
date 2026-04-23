def __call__(
      self,
      raw_boxes: Mapping[str, tf.Tensor],
      raw_scores: Mapping[str, tf.Tensor],
      anchor_boxes: Mapping[str, tf.Tensor],
      image_shape: tf.Tensor,
      raw_attributes: Optional[Mapping[str, tf.Tensor]] = None,
  ) -> Mapping[str, Any]:
    """Generates final detections.

    Args:
      raw_boxes: A `dict` with keys representing FPN levels and values
        representing box tenors of shape `[batch, feature_h, feature_w,
        num_anchors * 4]`.
      raw_scores: A `dict` with keys representing FPN levels and values
        representing logit tensors of shape `[batch, feature_h, feature_w,
        num_anchors * num_classes]`.
      anchor_boxes: A `dict` with keys representing FPN levels and values
        representing anchor tenors of shape `[batch_size, K, 4]` representing
        the corresponding anchor boxes w.r.t `box_outputs`.
      image_shape: A `tf.Tensor` of shape of [batch_size, 2] storing the image
        height and width w.r.t. the scaled image, i.e. the same image space as
        `box_outputs` and `anchor_boxes`.
      raw_attributes: If not None, a `dict` of (attribute_name,
        attribute_prediction) pairs. `attribute_prediction` is a dict that
        contains keys representing FPN levels and values representing tenors of
        shape `[batch, feature_h, feature_w, num_anchors * attribute_size]`.

    Returns:
      If `apply_nms` = True, the return is a dictionary with keys:
        `detection_boxes`: A `float` tf.Tensor of shape
          [batch, max_num_detections, 4] representing top detected boxes in
          [y1, x1, y2, x2].
        `detection_scores`: A `float` tf.Tensor of shape
          [batch, max_num_detections] representing sorted confidence scores for
          detected boxes. The values are between [0, 1].
        `detection_classes`: An `int` tf.Tensor of shape
          [batch, max_num_detections] representing classes for detected boxes.
        `num_detections`: An `int` tf.Tensor of shape [batch] only the first
          `num_detections` boxes are valid detections
        `detection_attributes`: A dict. Values of the dict is a `float`
          tf.Tensor of shape [batch, max_num_detections, attribute_size]
          representing attribute predictions for detected boxes.
      If `apply_nms` = False, the return is a dictionary with following keys. If
      `return_decoded` = True, the following items will also be included even if
      `apply_nms` = True:
        `decoded_boxes`: A `float` tf.Tensor of shape [batch, num_raw_boxes, 4]
          representing all the decoded boxes.
        `decoded_box_scores`: A `float` tf.Tensor of shape
          [batch, num_raw_boxes] representing socres of all the decoded boxes.
        `decoded_box_attributes`: A dict. Values in the dict is a
          `float` tf.Tensor of shape [batch, num_raw_boxes, attribute_size]
          representing attribute predictions of all the decoded boxes.
    """
    if (
        self._config_dict['apply_nms']
        and self._config_dict['nms_version'] == 'tflite'
    ):
      boxes, classes, scores, num_detections = _generate_detections_tflite(
          raw_boxes,
          raw_scores,
          anchor_boxes,
          self.get_config()['tflite_post_processing_config'],
          self._config_dict['box_coder_weights'],
      )
      return {
          'detection_boxes': boxes,
          'detection_classes': classes,
          'detection_scores': scores,
          'num_detections': num_detections,
      }

    if self._config_dict['nms_version'] != 'v3':
      boxes, scores, attributes = self._decode_multilevel_outputs(
          raw_boxes, raw_scores, anchor_boxes, image_shape, raw_attributes
      )
    else:
      attributes = None
      boxes, scores = self._decode_multilevel_outputs_and_pre_nms_top_k(
          raw_boxes, raw_scores, anchor_boxes, image_shape
      )

    decoded_results = {
        'decoded_boxes': boxes,
        'decoded_box_scores': scores,
        'decoded_box_attributes': attributes,
    }

    if not self._config_dict['apply_nms']:
      return decoded_results

    # Optionally force the NMS to run on CPU.
    if self._config_dict['use_cpu_nms']:
      nms_context = tf.device('cpu:0')
    else:
      nms_context = contextlib.nullcontext()

    with nms_context:
      if raw_attributes and (self._config_dict['nms_version'] != 'v1'):
        raise ValueError(
            'Attribute learning is only supported for NMSv1 but NMS {} is used.'
            .format(self._config_dict['nms_version'])
        )
      if self._config_dict['nms_version'] == 'batched':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections) = (
            _generate_detections_batched(
                boxes,
                scores,
                self._config_dict['pre_nms_score_threshold'],
                self._config_dict['nms_iou_threshold'],
                self._config_dict['max_num_detections'],
            )
        )
        # Set `nmsed_attributes` to None for batched NMS.
        nmsed_attributes = {}
      elif self._config_dict['nms_version'] == 'v1':
        (
            nmsed_boxes,
            nmsed_scores,
            nmsed_classes,
            valid_detections,
            nmsed_attributes,
        ) = _generate_detections_v1(
            boxes,
            scores,
            attributes=attributes if raw_attributes else None,
            pre_nms_top_k=self._config_dict['pre_nms_top_k'],
            pre_nms_score_threshold=self._config_dict[
                'pre_nms_score_threshold'
            ],
            nms_iou_threshold=self._config_dict['nms_iou_threshold'],
            max_num_detections=self._config_dict['max_num_detections'],
            soft_nms_sigma=self._config_dict['soft_nms_sigma'],
        )
      elif self._config_dict['nms_version'] == 'v2':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections) = (
            _generate_detections_v2(
                boxes,
                scores,
                pre_nms_top_k=self._config_dict['pre_nms_top_k'],
                pre_nms_score_threshold=self._config_dict[
                    'pre_nms_score_threshold'
                ],
                nms_iou_threshold=self._config_dict['nms_iou_threshold'],
                max_num_detections=self._config_dict['max_num_detections'],
                use_class_agnostic_nms=self._config_dict[
                    'use_class_agnostic_nms'
                ],
            )
        )
        # Set `nmsed_attributes` to None for v2.
        nmsed_attributes = {}
      elif self._config_dict['nms_version'] == 'v3':
        (nmsed_boxes, nmsed_scores, nmsed_classes, valid_detections) = (
            _generate_detections_v3(
                boxes,
                scores,
                pre_nms_score_threshold=self._config_dict[
                    'pre_nms_score_threshold'
                ],
                nms_iou_threshold=self._config_dict['nms_iou_threshold'],
                max_num_detections=self._config_dict['max_num_detections'],
                refinements=self._config_dict.get('nms_v3_refinements', 2),
            )
        )
        # Set `nmsed_attributes` to None for v3.
        nmsed_attributes = {}
      else:
        raise ValueError(
            'NMS version {} not supported.'.format(
                self._config_dict['nms_version']
            )
        )

    # Adds 1 to offset the background class which has index 0.
    nmsed_classes += 1

    return {
        **(decoded_results if self._config_dict['return_decoded'] else {}),
        'num_detections': valid_detections,
        'detection_boxes': nmsed_boxes,
        'detection_classes': nmsed_classes,
        'detection_scores': nmsed_scores,
        'detection_attributes': nmsed_attributes,
    }