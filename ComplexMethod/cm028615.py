def call(
      self, inputs: Mapping[str, tf.Tensor]
  ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[Any, Dict[str, Any]]]:
    # Build multi level features.
    feats = {}
    for level in range(self._decoder_output_level,
                       self._config_dict['max_level'] + 1):
      if level == self._decoder_output_level:
        x = inputs[str(level)]
      else:
        x = self._convs[str(level)](feats[level - 1])
      feats[level] = x

    # Get multi level detection.
    scores = {}
    boxes = {}
    if self._config_dict['attribute_heads']:
      attributes = {
          att_config['name']: {}
          for att_config in self._config_dict['attribute_heads']
      }
    else:
      attributes = {}

    for level in range(self._config_dict['min_level'],
                       self._config_dict['max_level'] + 1):
      # The branch to predict box classes.
      scores[str(level)] = self._classifier(feats[level])
      # The branch to predict boxes.
      boxes[str(level)] = self._box_regressor(feats[level])
      # The branches to predict box attributes.
      if self._config_dict['attribute_heads']:
        for att_config in self._config_dict['attribute_heads']:
          att_name = att_config['name']
          attributes[att_name][str(level)] = self._att_predictors[att_name](
              feats[level])

    return scores, boxes, attributes