def call(self, features: Mapping[str, tf.Tensor]):
    """Forward pass of the RetinaNet quantized head.

    Args:
      features: A `dict` of `tf.Tensor` where
        - key: A `str` of the level of the multilevel features.
        - values: A `tf.Tensor`, the feature map tensors, whose shape is
            [batch, height_l, width_l, channels].

    Returns:
      scores: A `dict` of `tf.Tensor` which includes scores of the predictions.
        - key: A `str` of the level of the multilevel predictions.
        - values: A `tf.Tensor` of the box scores predicted from a particular
            feature level, whose shape is
            [batch, height_l, width_l, num_classes * num_anchors_per_location].
      boxes: A `dict` of `tf.Tensor` which includes coordinates of the
        predictions.
        - key: A `str` of the level of the multilevel predictions.
        - values: A `tf.Tensor` of the box scores predicted from a particular
            feature level, whose shape is
            [batch, height_l, width_l,
             num_params_per_anchor * num_anchors_per_location].
      attributes: a dict of (attribute_name, attribute_prediction). Each
        `attribute_prediction` is a dict of:
        - key: `str`, the level of the multilevel predictions.
        - values: `Tensor`, the box scores predicted from a particular feature
            level, whose shape is
            [batch, height_l, width_l,
            attribute_size * num_anchors_per_location].
        Can be an empty dictionary if no attribute learning is required.
    """
    scores = {}
    boxes = {}
    if self._config_dict['attribute_heads']:
      attributes = {
          att_config['name']: {}
          for att_config in self._config_dict['attribute_heads']
      }
    else:
      attributes = {}

    for i, level in enumerate(
        range(self._config_dict['min_level'],
              self._config_dict['max_level'] + 1)):
      this_level_features = features[str(level)]

      # class net.
      x = this_level_features
      for conv, norm in zip(self._cls_convs, self._cls_norms[i]):
        x = conv(x)
        x = norm(x)
        x = self._activation(x)
      scores[str(level)] = self._classifier(x)

      # box net.
      x = this_level_features
      for conv, norm in zip(self._box_convs, self._box_norms[i]):
        x = conv(x)
        x = norm(x)
        x = self._activation(x)
      boxes[str(level)] = self._box_regressor(x)

      # attribute nets.
      if self._config_dict['attribute_heads']:
        prediction_tower_output = {}
        for att_config in self._config_dict['attribute_heads']:
          att_name = att_config['name']

          def build_prediction_tower(atttribute_name, features, feature_level):
            x = features
            for conv, norm in zip(
                self._att_convs[atttribute_name],
                self._att_norms[atttribute_name][feature_level]):
              x = conv(x)
              x = norm(x)
              x = self._activation(x)
            return x

          prediction_tower_name = att_config['prediction_tower_name']
          if not prediction_tower_name:
            attributes[att_name][str(level)] = self._att_predictors[att_name](
                build_prediction_tower(att_name, this_level_features, i))
          else:
            if prediction_tower_name not in prediction_tower_output:
              prediction_tower_output[
                  prediction_tower_name] = build_prediction_tower(
                      att_name, this_level_features, i)
            attributes[att_name][str(level)] = self._att_predictors[att_name](
                prediction_tower_output[prediction_tower_name])

    return scores, boxes, attributes