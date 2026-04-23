def __init__(self,
               filters=1,
               kernel_size=(1, 1),
               strides=(1, 1),
               padding='same',
               dilation_rate=(1, 1),
               kernel_initializer='VarianceScaling',
               bias_initializer='zeros',
               bias_regularizer=None,
               kernel_regularizer=None,
               use_separable_conv=False,
               use_bn=True,
               use_sync_bn=False,
               norm_momentum=0.99,
               norm_epsilon=0.001,
               activation='leaky',
               leaky_alpha=0.1,
               **kwargs):
    """ConvBN initializer.

    Args:
      filters: integer for output depth, or the number of features to learn.
      kernel_size: integer or tuple for the shape of the weight matrix or kernel
        to learn.
      strides: integer of tuple how much to move the kernel after each kernel
        use.
      padding: string 'valid' or 'same', if same, then pad the image, else do
        not.
      dilation_rate: tuple to indicate how much to modulate kernel weights and
        how many pixels in a feature map to skip.
      kernel_initializer: string to indicate which function to use to initialize
        weights.
      bias_initializer: string to indicate which function to use to initialize
        bias.
      bias_regularizer: string to indicate which function to use to regularizer
        bias.
      kernel_regularizer: string to indicate which function to use to
        regularizer weights.
      use_separable_conv: `bool` wether to use separable convs.
      use_bn: boolean for whether to use batch normalization.
      use_sync_bn: boolean for whether sync batch normalization statistics
        of all batch norm layers to the models global statistics
        (across all input batches).
      norm_momentum: float for moment to use for batch normalization.
      norm_epsilon: float for batch normalization epsilon.
      activation: string or None for activation function to use in layer,
        if None activation is replaced by linear.
      leaky_alpha: float to use as alpha if activation function is leaky.
      **kwargs: Keyword Arguments.
    """

    # convolution params
    self._filters = filters
    self._kernel_size = kernel_size
    self._strides = strides
    self._padding = padding
    self._dilation_rate = dilation_rate

    if kernel_initializer == 'VarianceScaling':
      # to match pytorch initialization method
      self._kernel_initializer = tf_keras.initializers.VarianceScaling(
          scale=1 / 3, mode='fan_in', distribution='uniform')
    else:
      self._kernel_initializer = kernel_initializer

    self._bias_initializer = bias_initializer
    self._kernel_regularizer = kernel_regularizer

    self._bias_regularizer = bias_regularizer

    # batch normalization params
    self._use_bn = use_bn
    self._use_separable_conv = use_separable_conv
    self._use_sync_bn = use_sync_bn
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon

    ksize = self._kernel_size
    if not isinstance(ksize, List) and not isinstance(ksize, Tuple):
      ksize = [ksize]
    if use_separable_conv and not all([a == 1 for a in ksize]):
      self._conv_base = tf_keras.layers.SeparableConv2D
    else:
      self._conv_base = tf_keras.layers.Conv2D

    self._bn_base = tf_keras.layers.BatchNormalization

    if tf_keras.backend.image_data_format() == 'channels_last':
      # format: (batch_size, height, width, channels)
      self._bn_axis = -1
    else:
      # format: (batch_size, channels, width, height)
      self._bn_axis = 1

    # activation params
    self._activation = activation
    self._leaky_alpha = leaky_alpha
    self._fuse = False

    super().__init__(**kwargs)