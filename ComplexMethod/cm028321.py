def loss(self, prediction_dict, true_image_shapes, scope=None):
    """Compute scalar loss tensors with respect to provided groundtruth.

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
      confidences = None
      if self.groundtruth_has_field(fields.BoxListFields.confidences):
        confidences = self.groundtruth_lists(fields.BoxListFields.confidences)
      (batch_cls_targets, batch_cls_weights, batch_reg_targets,
       batch_reg_weights, batch_match) = self._assign_targets(
           self.groundtruth_lists(fields.BoxListFields.boxes),
           self.groundtruth_lists(fields.BoxListFields.classes),
           keypoints, weights, confidences)
      match_list = [matcher.Match(match) for match in tf.unstack(batch_match)]
      if self._add_summaries:
        self._summarize_target_assignment(
            self.groundtruth_lists(fields.BoxListFields.boxes), match_list)

      if self._random_example_sampler:
        batch_cls_per_anchor_weights = tf.reduce_mean(
            batch_cls_weights, axis=-1)
        batch_sampled_indicator = tf.cast(
            shape_utils.static_or_dynamic_map_fn(
                self._minibatch_subsample_fn,
                [batch_cls_targets, batch_cls_per_anchor_weights],
                dtype=tf.bool,
                parallel_iterations=self._parallel_iterations,
                back_prop=True), dtype=tf.float32)
        batch_reg_weights = tf.multiply(batch_sampled_indicator,
                                        batch_reg_weights)
        batch_cls_weights = tf.multiply(
            tf.expand_dims(batch_sampled_indicator, -1),
            batch_cls_weights)

      losses_mask = None
      if self.groundtruth_has_field(fields.InputDataFields.is_annotated):
        losses_mask = tf.stack(self.groundtruth_lists(
            fields.InputDataFields.is_annotated))


      location_losses = self._localization_loss(
          prediction_dict['box_encodings'],
          batch_reg_targets,
          ignore_nan_targets=True,
          weights=batch_reg_weights,
          losses_mask=losses_mask)

      cls_losses = self._classification_loss(
          prediction_dict['class_predictions_with_background'],
          batch_cls_targets,
          weights=batch_cls_weights,
          losses_mask=losses_mask)

      if self._expected_loss_weights_fn:
        # Need to compute losses for assigned targets against the
        # unmatched_class_label as well as their assigned targets.
        # simplest thing (but wasteful) is just to calculate all losses
        # twice
        batch_size, num_anchors, num_classes = batch_cls_targets.get_shape()
        unmatched_targets = tf.ones([batch_size, num_anchors, 1
                                    ]) * self._unmatched_class_label

        unmatched_cls_losses = self._classification_loss(
            prediction_dict['class_predictions_with_background'],
            unmatched_targets,
            weights=batch_cls_weights,
            losses_mask=losses_mask)

        if cls_losses.get_shape().ndims == 3:
          batch_size, num_anchors, num_classes = cls_losses.get_shape()
          cls_losses = tf.reshape(cls_losses, [batch_size, -1])
          unmatched_cls_losses = tf.reshape(unmatched_cls_losses,
                                            [batch_size, -1])
          batch_cls_targets = tf.reshape(
              batch_cls_targets, [batch_size, num_anchors * num_classes, -1])
          batch_cls_targets = tf.concat(
              [1 - batch_cls_targets, batch_cls_targets], axis=-1)

          location_losses = tf.tile(location_losses, [1, num_classes])

        foreground_weights, background_weights = (
            self._expected_loss_weights_fn(batch_cls_targets))

        cls_losses = (
            foreground_weights * cls_losses +
            background_weights * unmatched_cls_losses)

        location_losses *= foreground_weights

        classification_loss = tf.reduce_sum(cls_losses)
        localization_loss = tf.reduce_sum(location_losses)
      elif self._hard_example_miner:
        cls_losses = ops.reduce_sum_trailing_dimensions(cls_losses, ndims=2)
        (localization_loss, classification_loss) = self._apply_hard_mining(
            location_losses, cls_losses, prediction_dict, match_list)
        if self._add_summaries:
          self._hard_example_miner.summarize()
      else:
        cls_losses = ops.reduce_sum_trailing_dimensions(cls_losses, ndims=2)
        localization_loss = tf.reduce_sum(location_losses)
        classification_loss = tf.reduce_sum(cls_losses)

      # Optionally normalize by number of positive matches
      normalizer = tf.constant(1.0, dtype=tf.float32)
      if self._normalize_loss_by_num_matches:
        normalizer = tf.maximum(tf.cast(tf.reduce_sum(batch_reg_weights),
                                        dtype=tf.float32),
                                1.0)

      localization_loss_normalizer = normalizer
      if self._normalize_loc_loss_by_codesize:
        localization_loss_normalizer *= self._box_coder.code_size
      localization_loss = tf.multiply((self._localization_loss_weight /
                                       localization_loss_normalizer),
                                      localization_loss,
                                      name='localization_loss')
      classification_loss = tf.multiply((self._classification_loss_weight /
                                         normalizer), classification_loss,
                                        name='classification_loss')

      loss_dict = {
          'Loss/localization_loss': localization_loss,
          'Loss/classification_loss': classification_loss
      }


    return loss_dict