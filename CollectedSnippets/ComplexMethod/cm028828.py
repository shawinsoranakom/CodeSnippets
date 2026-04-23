def _build_attribute_net(self, conv_op, bn_op):
    self._att_predictors = {}
    self._att_convs = {}
    self._att_norms = {}

    for att_config, att_predictor_kwargs in zip(
        self._config_dict['attribute_heads'], self._attribute_kwargs
    ):
      att_name = att_config['name']
      att_num_convs = (
          att_config.get('num_convs') or self._config_dict['num_convs']
      )
      att_num_filters = (
          att_config.get('num_filters') or self._config_dict['num_filters']
      )
      if att_num_convs < 0:
        raise ValueError(f'Invalid `num_convs` {att_num_convs} for {att_name}.')
      if att_num_filters < 0:
        raise ValueError(
            f'Invalid `num_filters` {att_num_filters} for {att_name}.'
        )
      att_conv_kwargs = self._conv_kwargs.copy()
      att_conv_kwargs['filters'] = att_num_filters
      att_convs_i = []
      att_norms_i = []

      # Build conv and norm layers.
      for level in range(
          self._config_dict['min_level'], self._config_dict['max_level'] + 1
      ):
        this_level_att_norms = []
        for i in range(att_num_convs):
          if level == self._config_dict['min_level']:
            att_conv_name = '{}-conv_{}'.format(att_name, i)
            att_convs_i.append(conv_op(name=att_conv_name, **att_conv_kwargs))
          att_norm_name = '{}-conv-norm_{}_{}'.format(att_name, level, i)
          this_level_att_norms.append(
              bn_op(name=att_norm_name, **self._bn_kwargs)
          )
        att_norms_i.append(this_level_att_norms)
      self._att_convs[att_name] = att_convs_i
      self._att_norms[att_name] = att_norms_i

      # Build the final prediction layer.
      self._att_predictors[att_name] = conv_op(
          name='{}_attributes'.format(att_name), **att_predictor_kwargs
      )