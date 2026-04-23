def __init__(
      self,
      in_filters: int,
      out_filters: int,
      expand_ratio: float,
      strides: int,
      middle_dw_downsample: bool = True,
      start_dw_kernel_size: int = 0,
      middle_dw_kernel_size: int = 3,
      end_dw_kernel_size: int = 0,
      stochastic_depth_drop_rate: float | None = None,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: tf_keras.regularizers.Regularizer | None = None,
      bias_regularizer: tf_keras.regularizers.Regularizer | None = None,
      activation: str = 'relu',
      depthwise_activation: str | None = None,
      use_sync_bn: bool = False,
      dilation_rate: int = 1,
      divisible_by: int = 1,
      regularize_depthwise: bool = False,
      use_residual: bool = True,
      use_layer_scale: bool = False,
      layer_scale_init_value: float = 1e-5,
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      output_intermediate_endpoints: bool = False,
      **kwargs,
  ):
    """Initializes a UniversalInvertedBottleneckBlock.

    This is an extension of IB with optional depthwise convs before expansion (
    "starting" conv) and after projection ("ending" conv). Both of these convs
    are executed without activation. The standard depthwise conv of IB ("middle"
    conv) is optional too. This last one is followed by an activation, as in
    standard IBs. Squeeze-and-Excite or fused types of IBs are not supported.

    Args:
      in_filters: The number of filters of the input tensor.
      out_filters: The number of filters of the output tensor.
      expand_ratio: The filter multiplier for the first inverted bottleneck
        stage.
      strides: The block stride. If greater than 1, this block will ultimately
        downsample the input.
      middle_dw_downsample: If True, downsample in the middle depthwise
        otherwise downsample in the starting one.
      start_dw_kernel_size: The kernel size of the starting depthwise. A value
        of zero means that no starting depthwise will be added.
      middle_dw_kernel_size: The kernel size of the middle depthwise. A value of
        zero means that no middle depthwise will be added.
      end_dw_kernel_size: The kernel size of the ending depthwise. A value of
        zero means that no ending depthwise will be added.
      stochastic_depth_drop_rate: If not None, drop rate for the stochastic
        depth layer.
      kernel_initializer: The name of the convolutional layer
        kernel_initializer.
      kernel_regularizer: An optional kernel regularizer for the Conv2ds.
      bias_regularizer: An optional bias regularizer for the Conv2ds.
      activation: The name of the activation function.
      depthwise_activation: The name of the depthwise-only activation function.
      use_sync_bn: If True, use synchronized batch normalization.
      dilation_rate: The dilation rate to use for convolutions.
      divisible_by: Ensures all inner dimensions are divisible by this number.
      regularize_depthwise: If True, apply regularization on depthwise.
      use_residual: If True, include residual connection between input and
        output.
      use_layer_scale: If True, use layer scale.
      layer_scale_init_value: The initial layer scale value.
      norm_momentum: Momentum value for the moving average in normalization.
      norm_epsilon: Value added to variance to avoid dividing by zero in
        normalization.
      output_intermediate_endpoints: This block does not output any intermediate
        endpoint, but this argument is included for compatibility with other
        blocks.
      **kwargs: Additional keyword arguments to be passed.
    """
    super().__init__(**kwargs)
    logging.info(
        'UniversalInvertedBottleneckBlock with depthwise kernel sizes '
        '{%d, %d, %d}, strides=%d, and middle downsampling: %s',
        start_dw_kernel_size,
        middle_dw_kernel_size,
        end_dw_kernel_size,
        strides,
        middle_dw_downsample,
    )

    self._in_filters = in_filters
    self._out_filters = out_filters
    self._expand_ratio = expand_ratio
    self._strides = strides
    self._middle_dw_downsample = middle_dw_downsample
    self._start_dw_kernel_size = start_dw_kernel_size
    self._middle_dw_kernel_size = middle_dw_kernel_size
    self._end_dw_kernel_size = end_dw_kernel_size
    self._divisible_by = divisible_by
    self._stochastic_depth_drop_rate = stochastic_depth_drop_rate
    self._dilation_rate = dilation_rate
    self._use_sync_bn = use_sync_bn
    self._regularize_depthwise = regularize_depthwise
    self._use_residual = use_residual
    self._activation = activation
    self._depthwise_activation = depthwise_activation
    self._kernel_initializer = kernel_initializer
    self._use_layer_scale = use_layer_scale
    self._layer_scale_init_value = layer_scale_init_value
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._output_intermediate_endpoints = output_intermediate_endpoints

    if strides > 1:
      if middle_dw_downsample and not middle_dw_kernel_size:
        raise ValueError(
            'Requested downsampling at a non-existing middle depthwise.'
        )
      if not middle_dw_downsample and not start_dw_kernel_size:
        raise ValueError(
            'Requested downsampling at a non-existing starting depthwise.'
        )

    if use_sync_bn:
      self._norm = tf_keras.layers.experimental.SyncBatchNormalization
    else:
      self._norm = tf_keras.layers.BatchNormalization
    if tf_keras.backend.image_data_format() == 'channels_last':
      self._bn_axis = -1
    else:
      self._bn_axis = 1
    if not depthwise_activation:
      self._depthwise_activation = activation
    if regularize_depthwise:
      self._depthsize_regularizer = kernel_regularizer
    else:
      self._depthsize_regularizer = None