def __init__(
      self,
      model_id: int,
      input_specs: tf_keras.layers.InputSpec = layers.InputSpec(
          shape=[None, None, None, 3]),
      depth_multiplier: float = 1.0,
      stem_type: str = 'v0',
      resnetd_shortcut: bool = False,
      replace_stem_max_pool: bool = False,
      se_ratio: Optional[float] = None,
      init_stochastic_depth_rate: float = 0.0,
      upsample_repeats: Optional[List[int]] = None,
      upsample_filters: Optional[List[int]] = None,
      upsample_kernel_sizes: Optional[List[int]] = None,
      scale_stem: bool = True,
      activation: str = 'relu',
      use_sync_bn: bool = False,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bias_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      bn_trainable: bool = True,
      classification_output: bool = False,
      **kwargs):
    """Initializes a ResNet model.

    Args:
      model_id: An `int` of the depth of ResNet backbone model.
      input_specs: A `tf_keras.layers.InputSpec` of the input tensor.
      depth_multiplier: A `float` of the depth multiplier to uniformaly scale up
        all layers in channel size. This argument is also referred to as
        `width_multiplier` in (https://arxiv.org/abs/2103.07579).
      stem_type: A `str` of stem type of ResNet. Default to `v0`. If set to
        `v1`, use ResNet-D type stem (https://arxiv.org/abs/1812.01187).
      resnetd_shortcut: A `bool` of whether to use ResNet-D shortcut in
        downsampling blocks.
      replace_stem_max_pool: A `bool` of whether to replace the max pool in stem
        with a stride-2 conv,
      se_ratio: A `float` or None. Ratio of the Squeeze-and-Excitation layer.
      init_stochastic_depth_rate: A `float` of initial stochastic depth rate.
      upsample_repeats: A `list` for upsample repeats of the ConvNext blocks for
        each level starting from L5, then L4, and so on.
      upsample_filters: A `list` for the upsample filter sizes for the ConvNext
        blocks for each level.
      upsample_kernel_sizes: A `list` for upsample kernel sizes for the ConvNext
        blocks for each level.
      scale_stem: A `bool` of whether to scale stem layers.
      activation: A `str` name of the activation function.
      use_sync_bn: If True, use synchronized batch normalization.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A small `float` added to variance to avoid dividing by zero.
      kernel_initializer: A str for kernel initializer of convolutional layers.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default to None.
      bias_regularizer: A `tf_keras.regularizers.Regularizer` object for Conv2D.
        Default to None.
      bn_trainable: A `bool` that indicates whether batch norm layers should be
        trainable. Default to True.
      classification_output: A `bool` to output the correct level needed for
        classification (L3), only set to True for pretraining.
      **kwargs: Additional keyword arguments to be passed.
    """
    self._model_id = model_id
    self._input_specs = input_specs
    self._depth_multiplier = depth_multiplier
    self._stem_type = stem_type
    self._resnetd_shortcut = resnetd_shortcut
    self._replace_stem_max_pool = replace_stem_max_pool
    self._se_ratio = se_ratio
    self._init_stochastic_depth_rate = init_stochastic_depth_rate
    self._upsample_repeats = upsample_repeats
    self._upsample_filters = upsample_filters
    self._upsample_kernel_sizes = upsample_kernel_sizes
    self._scale_stem = scale_stem
    self._use_sync_bn = use_sync_bn
    self._activation = activation
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    if use_sync_bn:
      self._norm = layers.experimental.SyncBatchNormalization
    else:
      self._norm = layers.BatchNormalization
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._bn_trainable = bn_trainable
    self._classification_output = classification_output

    if tf_keras.backend.image_data_format() == 'channels_last':
      bn_axis = -1
    else:
      bn_axis = 1

    # Build ResNet.
    inputs = tf_keras.Input(shape=input_specs.shape[1:])

    stem_depth_multiplier = self._depth_multiplier if scale_stem else 1.0
    if stem_type == 'v0':
      x = layers.Conv2D(
          filters=int(64 * stem_depth_multiplier),
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
          trainable=bn_trainable)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
    elif stem_type == 'v1':
      x = layers.Conv2D(
          filters=int(32 * stem_depth_multiplier),
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
          trainable=bn_trainable)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
      x = layers.Conv2D(
          filters=int(32 * stem_depth_multiplier),
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
          trainable=bn_trainable)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
      x = layers.Conv2D(
          filters=int(64 * stem_depth_multiplier),
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
          trainable=bn_trainable)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
    else:
      raise ValueError('Stem type {} not supported.'.format(stem_type))

    if replace_stem_max_pool:
      x = layers.Conv2D(
          filters=int(64 * self._depth_multiplier),
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
          trainable=bn_trainable)(
              x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
    else:
      x = layers.MaxPool2D(pool_size=3, strides=2, padding='same')(x)

    endpoints = {}
    for i, spec in enumerate(RESNET_SPECS[model_id]):
      if spec[0] == 'residual':
        block_fn = nn_blocks.ResidualBlock
      elif spec[0] == 'bottleneck':
        block_fn = nn_blocks.BottleneckBlock
      else:
        raise ValueError('Block fn `{}` is not supported.'.format(spec[0]))
      x = self._block_group(
          inputs=x,
          filters=int(spec[1] * self._depth_multiplier),
          strides=(1 if i == 0 else 2),
          block_fn=block_fn,
          block_repeats=spec[2],
          stochastic_depth_drop_rate=nn_layers.get_stochastic_depth_rate(
              self._init_stochastic_depth_rate, i + 2, 8),
          name='block_group_l{}'.format(i + 2))
      endpoints[str(i + 2)] = x

    norm_layer = lambda: tf_keras.layers.LayerNormalization(epsilon=1e-6)
    for i in range(len(upsample_filters)):
      backbone_feature = layers.Conv2D(
          filters=int(upsample_filters[i] * stem_depth_multiplier),
          kernel_size=1,
          strides=1,
          use_bias=False,
          padding='same',
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer)(
              endpoints['{}'.format(5 - i)])
      backbone_feature = norm_layer()(backbone_feature)

      if i == 0:
        x = backbone_feature
      else:
        x = layers.Conv2D(
            filters=int(upsample_filters[i] * stem_depth_multiplier),
            kernel_size=1,
            strides=1,
            use_bias=False,
            padding='same',
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            bias_regularizer=self._bias_regularizer)(
                x)
        x = norm_layer()(x)

        x = spatial_transform_ops.nearest_upsampling(
            x, scale=2,
            use_keras_layer=True) + backbone_feature

      for _ in range(upsample_repeats[i]):
        x = ConvNeXtBlock(
            int(upsample_filters[i] * self._depth_multiplier),
            drop_rate=nn_layers.get_stochastic_depth_rate(
                self._init_stochastic_depth_rate, i + 6, 8),
            kernel_size=upsample_kernel_sizes[i])(x)
      x = tf_utils.get_activation(activation, use_keras_layer=True)(x)
      endpoints[str(5 - i)] = x

    if classification_output:
      endpoints['6'] = endpoints[str(5 - len(upsample_repeats) + 1)]

    self._output_specs = {l: endpoints[l].get_shape() for l in endpoints}

    super().__init__(inputs=inputs, outputs=endpoints, **kwargs)