def __init__(
      self,
      model_id: str = 'MobileNetV2',
      filter_size_scale: float = 1.0,
      input_specs: tf_keras.layers.InputSpec = layers.InputSpec(
          shape=[None, None, None, 3]
      ),
      # The followings are for hyper-parameter tuning.
      norm_momentum: float = 0.99,
      norm_epsilon: float = 0.001,
      kernel_initializer: str = 'VarianceScaling',
      kernel_regularizer: tf_keras.regularizers.Regularizer | None = None,
      bias_regularizer: tf_keras.regularizers.Regularizer | None = None,
      # The followings should be kept the same most of the times.
      output_stride: int | None = None,
      min_depth: int = 8,
      # divisible is not used in MobileNetV1.
      divisible_by: int = 8,
      stochastic_depth_drop_rate: float = 0.0,
      flat_stochastic_depth_drop_rate: bool = True,
      regularize_depthwise: bool = False,
      use_sync_bn: bool = False,
      # finegrain is not used in MobileNetV1.
      finegrain_classification_mode: bool = True,
      output_intermediate_endpoints: bool = False,
      **kwargs,
  ):
    """Initializes a MobileNet model.

    Args:
      model_id: A `str` of MobileNet version. The supported values are
        `MobileNetV1`, `MobileNetV2`, `MobileNetV3Large`, `MobileNetV3Small`,
        `MobileNetV3EdgeTPU`, `MobileNetMultiMAX` and `MobileNetMultiAVG`.
      filter_size_scale: A `float` of multiplier for the filters (number of
        channels) for all convolution ops. The value must be greater than zero.
        Typical usage will be to set this value in (0, 1) to reduce the number
        of parameters or computation cost of the model.
      input_specs: A `tf_keras.layers.InputSpec` of specs of the input tensor.
      norm_momentum: A `float` of normalization momentum for the moving average.
      norm_epsilon: A `float` added to variance to avoid dividing by zero.
      kernel_initializer: A `str` for kernel initializer of convolutional
        layers.
      kernel_regularizer: A `tf_keras.regularizers.Regularizer` object for
        Conv2D. Default to None.
      bias_regularizer: A `tf_keras.regularizers.Regularizer` object for Conv2D.
        Default to None.
      output_stride: An `int` that specifies the requested ratio of input to
        output spatial resolution. If not None, then we invoke atrous
        convolution if necessary to prevent the network from reducing the
        spatial resolution of activation maps. Allowed values are 8 (accurate
        fully convolutional mode), 16 (fast fully convolutional mode), 32
        (classification mode).
      min_depth: An `int` of minimum depth (number of channels) for all
        convolution ops. Enforced when filter_size_scale < 1, and not an active
        constraint when filter_size_scale >= 1.
      divisible_by: An `int` that ensures all inner dimensions are divisible by
        this number.
      stochastic_depth_drop_rate: A `float` of drop rate for drop connect layer.
      flat_stochastic_depth_drop_rate: A `bool`, indicating that the stochastic
        depth drop rate will be fixed and equal to all blocks.
      regularize_depthwise: If Ture, apply regularization on depthwise.
      use_sync_bn: If True, use synchronized batch normalization.
      finegrain_classification_mode: If True, the model will keep the last layer
        large even for small multipliers, following
        https://arxiv.org/abs/1801.04381.
      output_intermediate_endpoints: A `bool` of whether or not output the
        intermediate endpoints.
      **kwargs: Additional keyword arguments to be passed.
    """
    if model_id not in SUPPORTED_SPECS_MAP:
      raise ValueError('The MobileNet version {} '
                       'is not supported'.format(model_id))

    if filter_size_scale <= 0:
      raise ValueError('filter_size_scale is not greater than zero.')

    if output_stride is not None:
      if model_id == 'MobileNetV1':
        if output_stride not in [8, 16, 32]:
          raise ValueError('Only allowed output_stride values are 8, 16, 32.')
      else:
        if output_stride == 0 or (output_stride > 1 and output_stride % 2):
          raise ValueError('Output stride must be None, 1 or a multiple of 2.')

    self._model_id = model_id
    self._input_specs = input_specs
    self._filter_size_scale = filter_size_scale
    self._min_depth = min_depth
    self._output_stride = output_stride
    self._divisible_by = divisible_by
    self._stochastic_depth_drop_rate = stochastic_depth_drop_rate
    self._flat_stochastic_depth_drop_rate = flat_stochastic_depth_drop_rate
    self._regularize_depthwise = regularize_depthwise
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._use_sync_bn = use_sync_bn
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._finegrain_classification_mode = finegrain_classification_mode
    self._output_intermediate_endpoints = output_intermediate_endpoints

    inputs = tf_keras.Input(shape=input_specs.shape[1:])

    block_specs = SUPPORTED_SPECS_MAP.get(model_id)
    self._decoded_specs = block_spec_decoder(
        specs=block_specs,
        filter_size_scale=self._filter_size_scale,
        divisible_by=self._get_divisible_by(),
        finegrain_classification_mode=self._finegrain_classification_mode,
    )

    x, endpoints, next_endpoint_level = self._mobilenet_base(inputs=inputs)

    self._output_specs = {l: endpoints[l].get_shape() for l in endpoints}
    # Don't include the final layer in `self._output_specs` to support decoders.
    endpoints[str(next_endpoint_level)] = x

    super(MobileNet, self).__init__(
        inputs=inputs, outputs=endpoints, **kwargs)