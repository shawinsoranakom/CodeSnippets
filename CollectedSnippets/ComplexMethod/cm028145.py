def loss(self, prediction_dict, true_image_shapes, scope=None):
    """Computes scalar loss tensors with respect to provided groundtruth.

    Calling this function requires that groundtruth tensors have been
    provided via the provide_groundtruth function.

    Args:
      prediction_dict: a dictionary holding prediction tensors with
        1) box_encodings: 3-D float tensor of shape [batch_size, num_anchors,
          box_code_dimension] containing predicted boxes.
        2) class_predictions_with_background: 3-D float tensor of shape
          [batch_size, num_anchors, num_classes+1] containing class predictions
          (logits) for each of the anchors. Note that this tensor *includes*
          background class predictions.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is
        of the form [height, width, channels] indicating the shapes
        of true images in the resized images, as resized images can be padded
        with zeros.
      scope: Optional scope name.

    Returns:
      a dictionary mapping loss keys (`localization_loss` and
        `classification_loss`) to scalar tensors representing corresponding loss
        values.
    """
    with tf.name_scope(scope, 'Loss', prediction_dict.values()):
      keypoints = None
      if self.groundtruth_has_field(fields.BoxListFields.keypoints):
        keypoints = self.groundtruth_lists(fields.BoxListFields.keypoints)
      weights = None
      if self.groundtruth_has_field(fields.BoxListFields.weights):
        weights = self.groundtruth_lists(fields.BoxListFields.weights)
      (batch_cls_targets, batch_cls_weights, batch_reg_targets,
       batch_reg_weights, batch_match) = self._assign_targets(
           self.groundtruth_lists(fields.BoxListFields.boxes),
           self.groundtruth_lists(fields.BoxListFields.classes),
           keypoints, weights)
      match_list = [matcher.Match(match) for match in tf.unstack(batch_match)]
      if self._add_summaries:
        self._summarize_target_assignment(
            self.groundtruth_lists(fields.BoxListFields.boxes), match_list)
      location_losses = self._localization_loss(
          prediction_dict['box_encodings'],
          batch_reg_targets,
          ignore_nan_targets=True,
          weights=batch_reg_weights)
      cls_losses = ops.reduce_sum_trailing_dimensions(
          self._classification_loss(
              prediction_dict['class_predictions_with_background'],
              batch_cls_targets,
              weights=batch_cls_weights),
          ndims=2)

      if self._hard_example_miner:
        (loc_loss_list, cls_loss_list) = self._apply_hard_mining(
            location_losses, cls_losses, prediction_dict, match_list)
        localization_loss = tf.reduce_sum(tf.stack(loc_loss_list))
        classification_loss = tf.reduce_sum(tf.stack(cls_loss_list))

        if self._add_summaries:
          self._hard_example_miner.summarize()
      else:
        if self._add_summaries:
          class_ids = tf.argmax(batch_cls_targets, axis=2)
          flattened_class_ids = tf.reshape(class_ids, [-1])
          flattened_classification_losses = tf.reshape(cls_losses, [-1])
          self._summarize_anchor_classification_loss(
              flattened_class_ids, flattened_classification_losses)
        localization_loss = tf.reduce_sum(location_losses)
        classification_loss = tf.reduce_sum(cls_losses)

      # Optionally normalize by number of positive matches
      normalizer = tf.constant(1.0, dtype=tf.float32)
      if self._normalize_loss_by_num_matches:
        normalizer = tf.maximum(tf.to_float(tf.reduce_sum(batch_reg_weights)),
                                1.0)

      with tf.name_scope('localization_loss'):
        localization_loss_normalizer = normalizer
        if self._normalize_loc_loss_by_codesize:
          localization_loss_normalizer *= self._box_coder.code_size
        localization_loss = ((self._localization_loss_weight / (
            localization_loss_normalizer)) * localization_loss)
      with tf.name_scope('classification_loss'):
        classification_loss = ((self._classification_loss_weight / normalizer) *
                               classification_loss)

      loss_dict = {
          'localization_loss': localization_loss,
          'classification_loss': classification_loss
      }
    return loss_dict