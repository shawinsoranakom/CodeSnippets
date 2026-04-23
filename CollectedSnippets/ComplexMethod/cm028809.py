def _decode_multilevel_outputs(
      self,
      raw_boxes: Mapping[str, tf.Tensor],
      raw_scores: Mapping[str, tf.Tensor],
      anchor_boxes: Mapping[str, tf.Tensor],
      image_shape: tf.Tensor,
      raw_attributes: Optional[Mapping[str, tf.Tensor]] = None,
  ):
    """Collects dict of multilevel boxes, scores, attributes into lists."""
    boxes = []
    scores = []
    if raw_attributes:
      attributes = {att_name: [] for att_name in raw_attributes.keys()}
    else:
      attributes = {}

    levels = list(raw_boxes.keys())
    min_level = int(min(levels))
    max_level = int(max(levels))
    for i in range(min_level, max_level + 1):
      raw_boxes_i = raw_boxes[str(i)]
      raw_scores_i = raw_scores[str(i)]
      batch_size = tf.shape(raw_boxes_i)[0]
      (_, feature_h_i, feature_w_i, num_anchors_per_locations_times_4) = (
          raw_boxes_i.get_shape().as_list()
      )
      num_locations = feature_h_i * feature_w_i
      num_anchors_per_locations = num_anchors_per_locations_times_4 // 4
      num_classes = (
          raw_scores_i.get_shape().as_list()[-1] // num_anchors_per_locations
      )

      # Applies score transformation and remove the implicit background class.
      scores_i = tf.sigmoid(
          tf.reshape(
              raw_scores_i,
              [
                  batch_size,
                  num_locations * num_anchors_per_locations,
                  num_classes,
              ],
          )
      )
      scores_i = tf.slice(scores_i, [0, 0, 1], [-1, -1, -1])

      # Box decoding.
      # The anchor boxes are shared for all data in a batch.
      # One stage detector only supports class agnostic box regression.
      anchor_boxes_i = tf.reshape(
          anchor_boxes[str(i)],
          [batch_size, num_locations * num_anchors_per_locations, 4],
      )
      raw_boxes_i = tf.reshape(
          raw_boxes_i,
          [batch_size, num_locations * num_anchors_per_locations, 4],
      )
      boxes_i = box_ops.decode_boxes(
          raw_boxes_i,
          anchor_boxes_i,
          weights=self._config_dict['box_coder_weights'],
      )

      # Box clipping.
      if image_shape is not None:
        boxes_i = box_ops.clip_boxes(
            boxes_i, tf.expand_dims(image_shape, axis=1)
        )

      boxes.append(boxes_i)
      scores.append(scores_i)

      if raw_attributes:
        for att_name, raw_att in raw_attributes.items():
          attribute_size = (
              raw_att[str(i)].get_shape().as_list()[-1]
              // num_anchors_per_locations
          )
          att_i = tf.reshape(
              raw_att[str(i)],
              [
                  batch_size,
                  num_locations * num_anchors_per_locations,
                  attribute_size,
              ],
          )
          attributes[att_name].append(att_i)

    boxes = tf.concat(boxes, axis=1)
    boxes = tf.expand_dims(boxes, axis=2)
    scores = tf.concat(scores, axis=1)

    if raw_attributes:
      for att_name in raw_attributes.keys():
        attributes[att_name] = tf.concat(attributes[att_name], axis=1)
        attributes[att_name] = tf.expand_dims(attributes[att_name], axis=2)

    return boxes, scores, attributes