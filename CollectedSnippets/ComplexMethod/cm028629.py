def __init__(self,
               filters: int,
               kernel_size: tuple[int, int],
               groups: int,
               batch_norm_layer: Optional[tf_keras.layers.Layer] = None,
               bn_epsilon: float = 1e-3,
               bn_momentum: float = 0.99,
               data_format: str = 'channels_last',
               padding: str = 'valid',
               **kwargs: Any) -> tf_keras.Model:
    """Creates a 2D group convolution layer as a keras model.

    Args:
      filters: Integer, the dimensionality of the output space (i.e. the number
        of output filters in the convolution).
      kernel_size: An integer or tuple/list of 2 integers, specifying the height
        and width of the 2D convolution window. Can be a single integer to
        specify the same value for all spatial dimensions.
      groups: The number of input/output channel groups.
      batch_norm_layer: The batch normalization layer to use. This is typically
        tf_keras.layer.BatchNormalization or a derived class.
      bn_epsilon: Batch normalization epsilon.
      bn_momentum: Momentum used for moving average in batch normalization.
      data_format: The ordering of the dimensions in the inputs. `channels_last`
        corresponds to inputs with shape `(batch_size, height, width, channels)`
      padding: one of `"valid"` or `"same"` (case-insensitive).
      **kwargs: Additional keyword arguments passed to the underlying conv
        layers.

    Raises:
      ValueError: if groups < 1 or groups > filters
      ValueError: if `batch_norm_layer` is not a callable when provided.
      ValueError: if `data_format` is not channels_last
      ValueError: if `padding` is not `same` or `valid`.
    """
    super().__init__()
    self.conv_layers = []
    self.bn_layers = []
    per_conv_filter_size = filters / groups

    if groups <= 1 or groups >= filters:
      raise ValueError('Number of groups should be greater than 1 and less '
                       'than the output filters.')

    self.batch_norm_layer = batch_norm_layer
    self.use_batch_norm = False
    if self.batch_norm_layer is not None:
      if not inspect.isclass(self.batch_norm_layer):  # pytype: disable=not-supported-yet
        raise ValueError('batch_norm_layer is not a class.')
      self.use_batch_norm = True

    if 'activation' in kwargs.keys():
      self.activation = tf_keras.activations.get(kwargs['activation'])
      kwargs.pop('activation')
    else:
      self.activation = None

    if data_format != 'channels_last':
      raise ValueError(
          'GroupConv2D expects input to be in channels_last format.')

    if padding.lower() not in ('same', 'valid'):
      raise ValueError('Valid padding options are : same, or valid.')

    self._groups = groups
    for _ in range(self._groups):
      # Override the activation so that batchnorm can be applied after the conv.
      self.conv_layers.append(
          tf_keras.layers.Conv2D(per_conv_filter_size, kernel_size, **kwargs))

    if self.use_batch_norm:
      for _ in range(self._groups):
        self.bn_layers.append(
            self.batch_norm_layer(
                axis=-1, momentum=bn_momentum, epsilon=bn_epsilon))