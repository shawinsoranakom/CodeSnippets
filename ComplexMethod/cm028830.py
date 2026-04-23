def __init__(
      self,
      input_specs: Mapping[str, tf.TensorShape],
      min_level: int = 3,
      max_level: int = 7,
      block_specs: Optional[List[BlockSpec]] = None,
      num_filters: int = 256,
      num_repeats: int = 5,
      use_separable_conv: bool = False,
      activation: str = 'relu',
      use_sync_bn: bool = False,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bias_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      **kwargs):
    """Initializes a NAS-FPN model.

    Args:
      input_specs: A `dict` of input specifications. A dictionary consists of
        {level: TensorShape} from a backbone.
      min_level: An `int` of minimum level in FPN output feature maps.
      max_level: An `int` of maximum level in FPN output feature maps.
      block_specs: a list of BlockSpec objects that specifies the NAS-FPN
        network topology. By default, the previously discovered architecture is
        used.
      num_filters: An `int` number of filters in FPN layers.
      num_repeats: number of repeats for feature pyramid network.
      use_separable_conv: A `bool`.  If True use separable convolution for
        convolution in FPN layers.
      activation: A `str` name of the activation function.
      use_sync_bn: A `bool`. If True, use synchronized batch normalization.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A `float` added to variance to avoid dividing by zero.
      kernel_initializer: A `str` name of kernel_initializer for convolutional
        layers.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default is None.
      bias_regularizer: A `tf_keras.regularizers.Regularizer` object for Conv2D.
      **kwargs: Additional keyword arguments to be passed.
    """
    self._config_dict = {
        'input_specs': input_specs,
        'min_level': min_level,
        'max_level': max_level,
        'num_filters': num_filters,
        'num_repeats': num_repeats,
        'use_separable_conv': use_separable_conv,
        'activation': activation,
        'use_sync_bn': use_sync_bn,
        'norm_momentum': norm_momentum,
        'norm_epsilon': norm_epsilon,
        'kernel_initializer': kernel_initializer,
        'kernel_regularizer': kernel_regularizer,
        'bias_regularizer': bias_regularizer,
    }
    self._min_level = min_level
    self._max_level = max_level
    self._block_specs = (
        build_block_specs() if block_specs is None else block_specs
    )
    self._num_repeats = num_repeats
    self._conv_op = (tf_keras.layers.SeparableConv2D
                     if self._config_dict['use_separable_conv']
                     else tf_keras.layers.Conv2D)
    self._norm_op = tf_keras.layers.BatchNormalization
    if tf_keras.backend.image_data_format() == 'channels_last':
      self._bn_axis = -1
    else:
      self._bn_axis = 1
    self._norm_kwargs = {
        'axis': self._bn_axis,
        'momentum': self._config_dict['norm_momentum'],
        'epsilon': self._config_dict['norm_epsilon'],
        'synchronized': self._config_dict['use_sync_bn'],
    }
    self._activation = tf_utils.get_activation(activation)

    # Gets input feature pyramid from backbone.
    inputs = self._build_input_pyramid(input_specs, min_level)

    # Projects the input features.
    feats = []
    for level in range(self._min_level, self._max_level + 1):
      if str(level) in inputs.keys():
        feats.append(self._resample_feature_map(
            inputs[str(level)], level, level, self._config_dict['num_filters']))
      else:
        feats.append(self._resample_feature_map(
            feats[-1], level - 1, level, self._config_dict['num_filters']))

    # Repeatly builds the NAS-FPN modules.
    for _ in range(self._num_repeats):
      output_feats = self._build_feature_pyramid(feats)
      feats = [output_feats[level]
               for level in range(self._min_level, self._max_level + 1)]

    self._output_specs = {
        str(level): output_feats[level].get_shape()
        for level in range(min_level, max_level + 1)
    }
    output_feats = {str(level): output_feats[level]
                    for level in output_feats.keys()}
    super(NASFPN, self).__init__(inputs=inputs, outputs=output_feats, **kwargs)