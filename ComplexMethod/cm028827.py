def _build_prediction_tower(
      self, net_name, predictor_name, conv_op, bn_op, predictor_kwargs
  ):
    """Builds the prediction tower. Convs across levels can be shared or not."""
    convs = []
    norms = []
    for level in range(
        self._config_dict['min_level'], self._config_dict['max_level'] + 1
    ):
      if not self._config_dict['share_level_convs']:
        this_level_convs = []
      this_level_norms = []
      for i in range(self._config_dict['num_convs']):
        conv_kwargs = self._conv_kwargs_new_kernel_init(self._conv_kwargs)
        if not self._config_dict['share_level_convs']:
          # Do not share convs.
          this_level_convs.append(
              conv_op(name=f'{net_name}-conv_{level}_{i}', **conv_kwargs)
          )
        elif level == self._config_dict['min_level']:
          convs.append(conv_op(name=f'{net_name}-conv_{i}', **conv_kwargs))
        this_level_norms.append(
            bn_op(name=f'{net_name}-conv-norm_{level}_{i}', **self._bn_kwargs)
        )
      norms.append(this_level_norms)
      if not self._config_dict['share_level_convs']:
        convs.append(this_level_convs)

    # Create predictors after additional convs.
    if self._config_dict['share_level_convs']:
      predictors = conv_op(name=predictor_name, **predictor_kwargs)
    else:
      predictors = []
      for level in range(
          self._config_dict['min_level'], self._config_dict['max_level'] + 1
      ):
        predictor_kwargs_level = predictor_kwargs.copy()
        if isinstance(predictor_kwargs_level['filters'], dict):
          predictor_kwargs_level['filters'] = predictor_kwargs_level['filters'][
              str(level)
          ]
        predictor_kwargs_level = self._conv_kwargs_new_kernel_init(
            predictor_kwargs_level
        )
        predictors.append(
            conv_op(name=f'{predictor_name}-{level}', **predictor_kwargs_level)
        )

    return convs, norms, predictors