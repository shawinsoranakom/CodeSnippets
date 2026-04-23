def __init__(
      self,
      model_id: int,
      output_stride: int,
      input_specs: tf_keras.layers.InputSpec = layers.InputSpec(
          shape=[None, None, None, 3]),
      stem_type: str = 'v0',
      resnetd_shortcut: bool = False,
      replace_stem_max_pool: bool = False,
      se_ratio: Optional[float] = None,
      init_stochastic_depth_rate: float = 0.0,
      multigrid: Optional[Tuple[int]] = None,
      last_stage_repeats: int = 1,
      activation: str = 'relu',
      use_sync_bn: bool = False,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bias_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      **kwargs):
    """Initializes a ResNet model with DeepLab modification.

    Args:
      model_id: An `int` specifies depth of ResNet backbone model.
      output_stride: An `int` of output stride, ratio of input to output
        resolution.
      input_specs: A `tf_keras.layers.InputSpec` of the input tensor.
      stem_type: A `str` of stem type. Can be `v0` or `v1`. `v1` replaces 7x7
        conv by 3 3x3 convs.
      resnetd_shortcut: A `bool` of whether to use ResNet-D shortcut in
        downsampling blocks.
      replace_stem_max_pool: A `bool` of whether to replace the max pool in stem
        with a stride-2 conv,
      se_ratio: A `float` or None. Ratio of the Squeeze-and-Excitation layer.
      init_stochastic_depth_rate: A `float` of initial stochastic depth rate.
      multigrid: A tuple of the same length as the number of blocks in the last
        resnet stage.
      last_stage_repeats: An `int` that specifies how many times last stage is
        repeated.
      activation: A `str` name of the activation function.
      use_sync_bn: If True, use synchronized batch normalization.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A `float` added to variance to avoid dividing by zero.
      kernel_initializer: A str for kernel initializer of convolutional layers.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default to None.
      bias_regularizer: A `tf_keras.regularizers.Regularizer` object for Conv2D.
        Default to None.
      **kwargs: Additional keyword arguments to be passed.
    """
    self._model_id = model_id
    self._output_stride = output_stride
    self._input_specs = input_specs
    self._use_sync_bn = use_sync_bn
    self._activation = activation
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._norm = layers.BatchNormalization
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._stem_type = stem_type
    self._resnetd_shortcut = resnetd_shortcut
    self._replace_stem_max_pool = replace_stem_max_pool
    self._se_ratio = se_ratio
    self._init_stochastic_depth_rate = init_stochastic_depth_rate

    if tf_keras.backend.image_data_format() == 'channels_last':
      bn_axis = -1
    else:
      bn_axis = 1

    # Build ResNet.
    inputs = tf_keras.Input(shape=input_specs.shape[1:])

    if stem_type == 'v0':
      x = layers.Conv2D(
          filters=64,
          kernel_size=7,
          strides=2,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              inputs)
      x = self._norm(
          axis=bn_axis,
          momentum=norm_momentum,
          epsilon=norm_epsilon,
          synchronized=use_sync_bn)(
              x)
      x = tf_utils.get_activation(activation)(x)
    elif stem_type == 'v1':
      x = layers.Conv2D(
          filters=64,
          kernel_size=3,
          strides=2,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              inputs)
      x = self._norm(
          axis=bn_axis,
          momentum=norm_momentum,
          epsilon=norm_epsilon,
          synchronized=use_sync_bn)(
              x)
      x = tf_utils.get_activation(activation)(x)
      x = layers.Conv2D(
          filters=64,
          kernel_size=3,
          strides=1,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              x)
      x = self._norm(
          axis=bn_axis,
          momentum=norm_momentum,
          epsilon=norm_epsilon,
          synchronized=use_sync_bn)(
              x)
      x = tf_utils.get_activation(activation)(x)
      x = layers.Conv2D(
          filters=128,
          kernel_size=3,
          strides=1,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              x)
      x = self._norm(
          axis=bn_axis,
          momentum=norm_momentum,
          epsilon=norm_epsilon,
          synchronized=use_sync_bn)(
              x)
      x = tf_utils.get_activation(activation)(x)
    else:
      raise ValueError('Stem type {} not supported.'.format(stem_type))

    if replace_stem_max_pool:
      x = layers.Conv2D(
          filters=64,
          kernel_size=3,
          strides=2,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              x)
      x = self._norm(
          axis=bn_axis,
          momentum=norm_momentum,
          epsilon=norm_epsilon,
          synchronized=use_sync_bn)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
    else:
      x = layers.MaxPool2D(pool_size=3, strides=2, padding='same')(x)

    normal_resnet_stage = int(math.log2(self._output_stride)) - 2

    endpoints = {}
    for i in range(normal_resnet_stage + 1):
      spec = RESNET_SPECS[model_id][i]
      if spec[0] == 'bottleneck':
        block_fn = nn_blocks.BottleneckBlock
      else:
        raise ValueError('Block fn `{}` is not supported.'.format(spec[0]))
      x = self._block_group(
          inputs=x,
          filters=spec[1],
          strides=(1 if i == 0 else 2),
          dilation_rate=1,
          block_fn=block_fn,
          block_repeats=spec[2],
          stochastic_depth_drop_rate=nn_layers.get_stochastic_depth_rate(
              self._init_stochastic_depth_rate, i + 2, 4 + last_stage_repeats),
          name='block_group_l{}'.format(i + 2))
      endpoints[str(i + 2)] = x

    dilation_rate = 2
    for i in range(normal_resnet_stage + 1, 3 + last_stage_repeats):
      spec = RESNET_SPECS[model_id][i] if i < 3 else RESNET_SPECS[model_id][-1]
      if spec[0] == 'bottleneck':
        block_fn = nn_blocks.BottleneckBlock
      else:
        raise ValueError('Block fn `{}` is not supported.'.format(spec[0]))
      x = self._block_group(
          inputs=x,
          filters=spec[1],
          strides=1,
          dilation_rate=dilation_rate,
          block_fn=block_fn,
          block_repeats=spec[2],
          stochastic_depth_drop_rate=nn_layers.get_stochastic_depth_rate(
              self._init_stochastic_depth_rate, i + 2, 4 + last_stage_repeats),
          multigrid=multigrid if i >= 3 else None,
          name='block_group_l{}'.format(i + 2))
      dilation_rate *= 2

    endpoints[str(normal_resnet_stage + 2)] = x

    self._output_specs = {l: endpoints[l].get_shape() for l in endpoints}

    super(DilatedResNet, self).__init__(
        inputs=inputs, outputs=endpoints, **kwargs)