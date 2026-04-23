def postprocess(self, prediction_dict, true_image_shapes):
    """Converts prediction tensors to final detections.

    This function converts raw predictions tensors to final detection results by
    slicing off the background class, decoding box predictions and applying
    non max suppression and clipping to the image window.

    See base class for output format conventions.  Note also that by default,
    scores are to be interpreted as logits, but if a score_conversion_fn is
    used, then scores are remapped (and may thus have a different
    interpretation).

    Args:
      prediction_dict: a dictionary holding prediction tensors with
        1) preprocessed_inputs: a [batch, height, width, channels] image
          tensor.
        2) box_encodings: 3-D float tensor of shape [batch_size, num_anchors,
          box_code_dimension] containing predicted boxes.
        3) class_predictions_with_background: 3-D float tensor of shape
          [batch_size, num_anchors, num_classes+1] containing class predictions
          (logits) for each of the anchors.  Note that this tensor *includes*
          background class predictions.
        4) mask_predictions: (optional) a 5-D float tensor of shape
          [batch_size, num_anchors, q, mask_height, mask_width]. `q` can be
          either number of classes or 1 depending on whether a separate mask is
          predicted per class.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is
        of the form [height, width, channels] indicating the shapes
        of true images in the resized images, as resized images can be padded
        with zeros. Or None, if the clip window should cover the full image.

    Returns:
      detections: a dictionary containing the following fields
        detection_boxes: [batch, max_detections, 4] tensor with post-processed
          detection boxes.
        detection_scores: [batch, max_detections] tensor with scalar scores for
          post-processed detection boxes.
        detection_multiclass_scores: [batch, max_detections,
          num_classes_with_background] tensor with class score distribution for
          post-processed detection boxes including background class if any.
        detection_classes: [batch, max_detections] tensor with classes for
          post-processed detection classes.
        detection_keypoints: [batch, max_detections, num_keypoints, 2] (if
          encoded in the prediction_dict 'box_encodings')
        detection_masks: [batch_size, max_detections, mask_height, mask_width]
          (optional)
        num_detections: [batch]
        raw_detection_boxes: [batch, total_detections, 4] tensor with decoded
          detection boxes before Non-Max Suppression.
        raw_detection_score: [batch, total_detections,
          num_classes_with_background] tensor of multi-class scores for raw
          detection boxes.
    Raises:
      ValueError: if prediction_dict does not contain `box_encodings` or
        `class_predictions_with_background` fields.
    """
    if ('box_encodings' not in prediction_dict or
        'class_predictions_with_background' not in prediction_dict):
      raise ValueError('prediction_dict does not contain expected entries.')
    if 'anchors' not in prediction_dict:
      prediction_dict['anchors'] = self.anchors.get()
    with tf.name_scope('Postprocessor'):
      preprocessed_images = prediction_dict['preprocessed_inputs']
      box_encodings = prediction_dict['box_encodings']
      box_encodings = tf.identity(box_encodings, 'raw_box_encodings')
      class_predictions_with_background = (
          prediction_dict['class_predictions_with_background'])
      detection_boxes, detection_keypoints = self._batch_decode(
          box_encodings, prediction_dict['anchors'])
      detection_boxes = tf.identity(detection_boxes, 'raw_box_locations')
      detection_boxes = tf.expand_dims(detection_boxes, axis=2)

      detection_scores_with_background = self._score_conversion_fn(
          class_predictions_with_background)
      detection_scores = tf.identity(detection_scores_with_background,
                                     'raw_box_scores')
      if self._add_background_class or self._explicit_background_class:
        detection_scores = tf.slice(detection_scores, [0, 0, 1], [-1, -1, -1])
      additional_fields = None

      batch_size = (
          shape_utils.combined_static_and_dynamic_shape(preprocessed_images)[0])

      if 'feature_maps' in prediction_dict:
        feature_map_list = []
        for feature_map in prediction_dict['feature_maps']:
          feature_map_list.append(tf.reshape(feature_map, [batch_size, -1]))
        box_features = tf.concat(feature_map_list, 1)
        box_features = tf.identity(box_features, 'raw_box_features')
      additional_fields = {
          'multiclass_scores': detection_scores_with_background
      }
      if self._anchors is not None:
        num_boxes = (self._anchors.num_boxes_static() or
                     self._anchors.num_boxes())
        anchor_indices = tf.range(num_boxes)
        batch_anchor_indices = tf.tile(
            tf.expand_dims(anchor_indices, 0), [batch_size, 1])
        # All additional fields need to be float.
        additional_fields.update({
            'anchor_indices': tf.cast(batch_anchor_indices, tf.float32),
        })
      if detection_keypoints is not None:
        detection_keypoints = tf.identity(
            detection_keypoints, 'raw_keypoint_locations')
        additional_fields[fields.BoxListFields.keypoints] = detection_keypoints

      (nmsed_boxes, nmsed_scores, nmsed_classes, nmsed_masks,
       nmsed_additional_fields,
       num_detections) = self._non_max_suppression_fn(
           detection_boxes,
           detection_scores,
           clip_window=self._compute_clip_window(
               preprocessed_images, true_image_shapes),
           additional_fields=additional_fields,
           masks=prediction_dict.get('mask_predictions'))

      detection_dict = {
          fields.DetectionResultFields.detection_boxes:
              nmsed_boxes,
          fields.DetectionResultFields.detection_scores:
              nmsed_scores,
          fields.DetectionResultFields.detection_classes:
              nmsed_classes,
          fields.DetectionResultFields.num_detections:
              tf.cast(num_detections, dtype=tf.float32),
          fields.DetectionResultFields.raw_detection_boxes:
              tf.squeeze(detection_boxes, axis=2),
          fields.DetectionResultFields.raw_detection_scores:
              detection_scores_with_background
      }
      if (nmsed_additional_fields is not None and
          fields.InputDataFields.multiclass_scores in nmsed_additional_fields):
        detection_dict[
            fields.DetectionResultFields.detection_multiclass_scores] = (
                nmsed_additional_fields[
                    fields.InputDataFields.multiclass_scores])
      if (nmsed_additional_fields is not None and
          'anchor_indices' in nmsed_additional_fields):
        detection_dict.update({
            fields.DetectionResultFields.detection_anchor_indices:
                tf.cast(nmsed_additional_fields['anchor_indices'], tf.int32),
        })
      if (nmsed_additional_fields is not None and
          fields.BoxListFields.keypoints in nmsed_additional_fields):
        detection_dict[fields.DetectionResultFields.detection_keypoints] = (
            nmsed_additional_fields[fields.BoxListFields.keypoints])
      if nmsed_masks is not None:
        detection_dict[
            fields.DetectionResultFields.detection_masks] = nmsed_masks
      return detection_dict