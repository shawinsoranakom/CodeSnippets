def build(self, input_shape: Union[tf.TensorShape, List[tf.TensorShape]]):
    """Creates the variables of the head."""
    if self._config_dict['use_separable_conv']:
      conv_op = helper.SeparableConv2DQuantized
    else:
      conv_op = helper.quantize_wrapped_layer(
          tf_keras.layers.Conv2D,
          configs.Default8BitConvQuantizeConfig(
              ['kernel'], ['activation'], False))
    conv_kwargs = {
        'filters': self._config_dict['num_filters'],
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.zeros_initializer(),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if not self._config_dict['use_separable_conv']:
      conv_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(
              stddev=0.01),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })

    base_bn_op = (tf_keras.layers.experimental.SyncBatchNormalization
                  if self._config_dict['use_sync_bn']
                  else tf_keras.layers.BatchNormalization)
    bn_op = helper.norm_by_activation(
        self._config_dict['activation'],
        helper.quantize_wrapped_layer(
            base_bn_op, configs.Default8BitOutputQuantizeConfig()),
        helper.quantize_wrapped_layer(
            base_bn_op, configs.NoOpQuantizeConfig()))

    bn_kwargs = {
        'axis': self._bn_axis,
        'momentum': self._config_dict['norm_momentum'],
        'epsilon': self._config_dict['norm_epsilon'],
    }

    # Class net.
    self._cls_convs = []
    self._cls_norms = []
    for level in range(
        self._config_dict['min_level'], self._config_dict['max_level'] + 1):
      this_level_cls_norms = []
      for i in range(self._config_dict['num_convs']):
        if level == self._config_dict['min_level']:
          cls_conv_name = 'classnet-conv_{}'.format(i)
          self._cls_convs.append(conv_op(name=cls_conv_name, **conv_kwargs))
        cls_norm_name = 'classnet-conv-norm_{}_{}'.format(level, i)
        this_level_cls_norms.append(bn_op(name=cls_norm_name, **bn_kwargs))
      self._cls_norms.append(this_level_cls_norms)

    classifier_kwargs = {
        'filters': (
            self._config_dict['num_classes'] *
            self._config_dict['num_anchors_per_location']),
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.constant_initializer(-np.log((1 - 0.01) / 0.01)),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if not self._config_dict['use_separable_conv']:
      classifier_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(stddev=1e-5),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })
    self._classifier = conv_op(
        name='scores', last_quantize=True, **classifier_kwargs)

    # Box net.
    self._box_convs = []
    self._box_norms = []
    for level in range(
        self._config_dict['min_level'], self._config_dict['max_level'] + 1):
      this_level_box_norms = []
      for i in range(self._config_dict['num_convs']):
        if level == self._config_dict['min_level']:
          box_conv_name = 'boxnet-conv_{}'.format(i)
          self._box_convs.append(conv_op(name=box_conv_name, **conv_kwargs))
        box_norm_name = 'boxnet-conv-norm_{}_{}'.format(level, i)
        this_level_box_norms.append(bn_op(name=box_norm_name, **bn_kwargs))
      self._box_norms.append(this_level_box_norms)

    box_regressor_kwargs = {
        'filters': (self._config_dict['num_params_per_anchor'] *
                    self._config_dict['num_anchors_per_location']),
        'kernel_size': 3,
        'padding': 'same',
        'bias_initializer': tf.zeros_initializer(),
        'bias_regularizer': self._config_dict['bias_regularizer'],
    }
    if not self._config_dict['use_separable_conv']:
      box_regressor_kwargs.update({
          'kernel_initializer': tf_keras.initializers.RandomNormal(
              stddev=1e-5),
          'kernel_regularizer': self._config_dict['kernel_regularizer'],
      })
    self._box_regressor = conv_op(
        name='boxes', last_quantize=True, **box_regressor_kwargs)

    # Attribute learning nets.
    if self._config_dict['attribute_heads']:
      self._att_predictors = {}
      self._att_convs = {}
      self._att_norms = {}

      for att_config in self._config_dict['attribute_heads']:
        att_name = att_config['name']
        att_type = att_config['type']
        att_size = att_config['size']
        att_convs_i = []
        att_norms_i = []

        # Build conv and norm layers.
        for level in range(self._config_dict['min_level'],
                           self._config_dict['max_level'] + 1):
          this_level_att_norms = []
          for i in range(self._config_dict['num_convs']):
            if level == self._config_dict['min_level']:
              att_conv_name = '{}-conv_{}'.format(att_name, i)
              att_convs_i.append(conv_op(name=att_conv_name, **conv_kwargs))
            att_norm_name = '{}-conv-norm_{}_{}'.format(att_name, level, i)
            this_level_att_norms.append(bn_op(name=att_norm_name, **bn_kwargs))
          att_norms_i.append(this_level_att_norms)
        self._att_convs[att_name] = att_convs_i
        self._att_norms[att_name] = att_norms_i

        # Build the final prediction layer.
        att_predictor_kwargs = {
            'filters':
                (att_size * self._config_dict['num_anchors_per_location']),
            'kernel_size': 3,
            'padding': 'same',
            'bias_initializer': tf.zeros_initializer(),
            'bias_regularizer': self._config_dict['bias_regularizer'],
        }
        if att_type == 'regression':
          att_predictor_kwargs.update(
              {'bias_initializer': tf.zeros_initializer()})
        elif att_type == 'classification':
          att_predictor_kwargs.update({
              'bias_initializer':
                  tf.constant_initializer(-np.log((1 - 0.01) / 0.01))
          })
        else:
          raise ValueError(
              'Attribute head type {} not supported.'.format(att_type))

        if not self._config_dict['use_separable_conv']:
          att_predictor_kwargs.update({
              'kernel_initializer':
                  tf_keras.initializers.RandomNormal(stddev=1e-5),
              'kernel_regularizer':
                  self._config_dict['kernel_regularizer'],
          })

        self._att_predictors[att_name] = conv_op(
            name='{}_attributes'.format(att_name), **att_predictor_kwargs)

    super().build(input_shape)