def generate_outputs(
      self,
      raw_scores: Dict[str, tf.Tensor],
      raw_boxes: Dict[str, tf.Tensor],
      raw_attributes: Dict[str, Dict[str, tf.Tensor]],
      image_shape: Optional[tf.Tensor] = None,
      anchor_boxes: Optional[Mapping[str, tf.Tensor]] = None,
      generate_detections: bool = False) -> Mapping[str, Any]:
    if not raw_attributes:
      raise ValueError('PointPillars model needs attribute heads.')
    # Clap heading to [-pi, pi]
    if 'heading' in raw_attributes:
      raw_attributes['heading'] = utils.clip_heading(raw_attributes['heading'])

    outputs = {
        'cls_outputs': raw_scores,
        'box_outputs': raw_boxes,
        'attribute_outputs': raw_attributes,
    }
    # Cast raw prediction to float32 for loss calculation.
    outputs = tf.nest.map_structure(lambda x: tf.cast(x, tf.float32), outputs)
    if not generate_detections:
      return outputs

    if image_shape is None:
      raise ValueError('Image_shape should not be None for evaluation.')
    if anchor_boxes is None:
      # Generate anchors if needed.
      anchor_boxes = utils.generate_anchors(
          self._min_level,
          self._max_level,
          self._image_size,
          self._anchor_sizes,
      )
      for l in anchor_boxes:
        anchor_boxes[l] = tf.tile(
            tf.expand_dims(anchor_boxes[l], axis=0),
            [tf.shape(image_shape)[0], 1, 1, 1])

    # Generate detected boxes.
    if not self._detection_generator.get_config()['apply_nms']:
      raise ValueError('An NMS algorithm is required for detection generator')
    detections = self._detection_generator(raw_boxes, raw_scores,
                                           anchor_boxes, image_shape,
                                           raw_attributes)
    outputs.update({
        'boxes': detections['detection_boxes'],
        'scores': detections['detection_scores'],
        'classes': detections['detection_classes'],
        'num_detections': detections['num_detections'],
        'attributes': detections['detection_attributes'],
    })
    return outputs