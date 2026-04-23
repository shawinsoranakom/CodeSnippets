def __init__(
      self,
      model_id: int,
      input_specs: tf_keras.layers.InputSpec = tf_keras.layers.InputSpec(
          shape=[None, None, None, 3]),
      activation: str = 'relu',
      use_sync_bn: bool = False,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: Optional[tf_keras.regularizers.Regularizer] = None,
      **kwargs):
    """Initializes a RevNet model.

    Args:
      model_id: An `int` of depth/id of ResNet backbone model.
      input_specs: A `tf_keras.layers.InputSpec` of the input tensor.
      activation: A `str` name of the activation function.
      use_sync_bn: If True, use synchronized batch normalization.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A `float` added to variance to avoid dividing by zero.
      kernel_initializer: A str for kernel initializer of convolutional layers.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default to None.
      **kwargs: Additional keyword arguments to be passed.
    """
    self._model_id = model_id
    self._input_specs = input_specs
    self._use_sync_bn = use_sync_bn
    self._activation = activation
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._norm = tf_keras.layers.BatchNormalization

    axis = -1 if tf_keras.backend.image_data_format() == 'channels_last' else 1

    # Build RevNet.
    inputs = tf_keras.Input(shape=input_specs.shape[1:])

    x = tf_keras.layers.Conv2D(
        filters=REVNET_SPECS[model_id][0][1],
        kernel_size=7, strides=2, use_bias=False, padding='same',
        kernel_initializer=self._kernel_initializer,
        kernel_regularizer=self._kernel_regularizer)(inputs)
    x = self._norm(
        axis=axis,
        momentum=norm_momentum,
        epsilon=norm_epsilon,
        synchronized=use_sync_bn)(x)
    x = tf_utils.get_activation(activation)(x)
    x = tf_keras.layers.MaxPool2D(pool_size=3, strides=2, padding='same')(x)

    endpoints = {}
    for i, spec in enumerate(REVNET_SPECS[model_id]):
      if spec[0] == 'residual':
        inner_block_fn = nn_blocks.ResidualInner
      elif spec[0] == 'bottleneck':
        inner_block_fn = nn_blocks.BottleneckResidualInner
      else:
        raise ValueError('Block fn `{}` is not supported.'.format(spec[0]))

      if spec[1] % 2 != 0:
        raise ValueError('Number of output filters must be even to ensure '
                         'splitting in channel dimension for reversible blocks')

      x = self._block_group(
          inputs=x,
          filters=spec[1],
          strides=(1 if i == 0 else 2),
          inner_block_fn=inner_block_fn,
          block_repeats=spec[2],
          batch_norm_first=(i != 0),  # Only skip on first block
          name='revblock_group_{}'.format(i + 2))
      endpoints[str(i + 2)] = x

    self._output_specs = {l: endpoints[l].get_shape() for l in endpoints}

    super(RevNet, self).__init__(inputs=inputs, outputs=endpoints, **kwargs)