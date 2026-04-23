def __init__(self,
               filters: int,
               kernel_size: Union[int, tuple[int, int]],
               groups: int,
               strides: tuple[int, int] = (1, 1),
               padding: str = 'valid',
               data_format: str = 'channels_last',
               dilation_rate: tuple[int, int] = (1, 1),
               activation: Any = None,
               use_bias: bool = True,
               kernel_initializer: Any = 'glorot_uniform',
               bias_initializer: Any = 'zeros',
               kernel_regularizer: Any = None,
               bias_regularizer: Any = None,
               activity_regularizer: Any = None,
               kernel_constraint: Any = None,
               bias_constraint: Any = None,
               batch_norm_layer: Optional[tf_keras.layers.Layer] = None,
               bn_epsilon: float = 1e-3,
               bn_momentum: float = 0.99,
               **kwargs: Any) -> tf_keras.layers.Layer:
    """Creates a 2D group convolution keras layer.

    Args:
      filters: Integer, the dimensionality of the output space (i.e. the number
        of output filters in the convolution).
      kernel_size: An integer or tuple/list of 2 integers, specifying the height
        and width of the 2D convolution window. Can be a single integer to
        specify the same value for all spatial dimensions.
      groups: The number of input/output channel groups.
      strides: An integer or tuple/list of n integers, specifying the stride
        length of the convolution. Specifying any stride value != 1 is
        incompatible with specifying any `dilation_rate` value != 1.
      padding: one of `"valid"` or `"same"` (case-insensitive).
      data_format: The ordering of the dimensions in the inputs. `channels_last`
        corresponds to inputs with shape `(batch_size, height, width, channels)`
      dilation_rate: an integer or tuple/list of 2 integers, specifying the
        dilation rate to use for dilated convolution. Can be a single integer to
        specify the same value for all spatial dimensions. Currently, specifying
        any `dilation_rate` value != 1 is incompatible with specifying any
        stride value != 1.
      activation: Activation function to use. If you don't specify anything, no
        activation is applied ( see `keras.activations`).
      use_bias: Boolean, whether the layer uses a bias vector.
      kernel_initializer: Initializer for the `kernel` weights matrix ( see
        `keras.initializers`).
      bias_initializer: Initializer for the bias vector ( see
        `keras.initializers`).
      kernel_regularizer: Regularizer function applied to the `kernel` weights
        matrix (see `keras.regularizers`).
      bias_regularizer: Regularizer function applied to the bias vector ( see
        `keras.regularizers`).
      activity_regularizer: Regularizer function applied to the output of the
        layer (its "activation") ( see `keras.regularizers`).
      kernel_constraint: Constraint function applied to the kernel matrix ( see
        `keras.constraints`).
      bias_constraint: Constraint function applied to the bias vector ( see
        `keras.constraints`).
      batch_norm_layer: The batch normalization layer to use. This is typically
        tf_keras.layer.BatchNormalization or a derived class.
      bn_epsilon: Batch normalization epsilon.
      bn_momentum: Momentum used for moving average in batch normalization.
      **kwargs: Additional keyword arguments.
    Input shape:
      4D tensor with shape: `(batch_size, rows, cols, channels)`
    Output shape:
      4D tensor with shape: `(batch_size, new_rows, new_cols, filters)` `rows`
        and `cols` values might have changed due to padding.

    Returns:
      A tensor of rank 4 representing
      `activation(GroupConv2D(inputs, kernel) + bias)`.

    Raises:
      ValueError: if groups < 1 or groups > filters
      ValueError: if data_format is not "channels_last".
      ValueError: if `padding` is not `same` or `valid`.
      ValueError: if `batch_norm_layer` is not a callable when provided.
      ValueError: when both `strides` > 1 and `dilation_rate` > 1.
    """
    if groups <= 1 or groups > filters:
      raise ValueError(f'Number of groups {groups} should be greater than 1 and'
                       f' less or equal than the output filters {filters}.')
    self._groups = groups
    if data_format != 'channels_last':
      raise ValueError(
          'GroupConv2D expects input to be in channels_last format.')

    if padding.lower() not in ('same', 'valid'):
      raise ValueError('Valid padding options are : same, or valid.')

    self.use_batch_norm = False
    if batch_norm_layer is not None:
      if not inspect.isclass(batch_norm_layer):
        raise ValueError('batch_norm_layer is not a class.')
      self.use_batch_norm = True
    self.bn_epsilon = bn_epsilon
    self.bn_momentum = bn_momentum
    self.batch_norm_layer = []
    if self.use_batch_norm:
      self.batch_norm_layer = [
          batch_norm_layer(
              axis=-1, momentum=self.bn_momentum, epsilon=self.bn_epsilon)
          for i in range(self._groups)
      ]

    super().__init__(
        filters=filters,
        kernel_size=kernel_size,
        strides=strides,
        padding=padding,
        data_format=data_format,
        dilation_rate=dilation_rate,
        activation=activation,
        use_bias=use_bias,
        kernel_initializer=kernel_initializer,
        bias_initializer=bias_initializer,
        kernel_regularizer=kernel_regularizer,
        bias_regularizer=bias_regularizer,
        activity_regularizer=activity_regularizer,
        kernel_constraint=kernel_constraint,
        bias_constraint=bias_constraint,
        groups=1,
        **kwargs)