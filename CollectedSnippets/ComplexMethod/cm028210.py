def _predict(self, image_features, num_predictions_per_location_list):
    """Computes encoded object locations and corresponding confidences.

    Args:
      image_features: A list of float tensors of shape [batch_size, height_i,
        width_i, channels_i] containing features for a batch of images.
      num_predictions_per_location_list: A list of integers representing the
        number of box predictions to be made per spatial location for each
        feature map.

    Returns:
      A dictionary containing:
        box_encodings: A list of float tensors of shape
          [batch_size, num_anchors_i, q, code_size] representing the location of
          the objects, where q is 1 or the number of classes. Each entry in the
          list corresponds to a feature map in the input `image_features` list.
        class_predictions_with_background: A list of float tensors of shape
          [batch_size, num_anchors_i, num_classes + 1] representing the class
          predictions for the proposals. Each entry in the list corresponds to a
          feature map in the input `image_features` list.
        (optional) Predictions from other heads.
    """
    predictions = {
        BOX_ENCODINGS: [],
        CLASS_PREDICTIONS_WITH_BACKGROUND: [],
    }
    for head_name in self._other_heads.keys():
      predictions[head_name] = []
    # TODO(rathodv): Come up with a better way to generate scope names
    # in box predictor once we have time to retrain all models in the zoo.
    # The following lines create scope names to be backwards compatible with the
    # existing checkpoints.
    box_predictor_scopes = [_NoopVariableScope()]
    if len(image_features) > 1:
      box_predictor_scopes = [
          tf.variable_scope('BoxPredictor_{}'.format(i))
          for i in range(len(image_features))
      ]
    for (image_feature,
         num_predictions_per_location, box_predictor_scope) in zip(
             image_features, num_predictions_per_location_list,
             box_predictor_scopes):
      net = image_feature
      with box_predictor_scope:
        with slim.arg_scope(self._conv_hyperparams_fn()):
          with slim.arg_scope([slim.dropout], is_training=self._is_training):
            # Add additional conv layers before the class predictor.
            features_depth = static_shape.get_depth(image_feature.get_shape())
            depth = max(min(features_depth, self._max_depth), self._min_depth)
            tf.logging.info('depth of additional conv before box predictor: {}'.
                            format(depth))
            if depth > 0 and self._num_layers_before_predictor > 0:
              for i in range(self._num_layers_before_predictor):
                net = slim.conv2d(
                    net,
                    depth, [1, 1],
                    reuse=tf.AUTO_REUSE,
                    scope='Conv2d_%d_1x1_%d' % (i, depth))
            sorted_keys = sorted(self._other_heads.keys())
            sorted_keys.append(BOX_ENCODINGS)
            sorted_keys.append(CLASS_PREDICTIONS_WITH_BACKGROUND)
            for head_name in sorted_keys:
              if head_name == BOX_ENCODINGS:
                head_obj = self._box_prediction_head
              elif head_name == CLASS_PREDICTIONS_WITH_BACKGROUND:
                head_obj = self._class_prediction_head
              else:
                head_obj = self._other_heads[head_name]
              prediction = head_obj.predict(
                  features=net,
                  num_predictions_per_location=num_predictions_per_location)
              predictions[head_name].append(prediction)
    return predictions