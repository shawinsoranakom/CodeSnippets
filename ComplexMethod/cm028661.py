def __init__(self,
               model_id: str = 'a0',
               causal: bool = False,
               use_positional_encoding: bool = False,
               conv_type: str = '3d',
               se_type: str = '3d',
               input_specs: Optional[tf_keras.layers.InputSpec] = None,
               activation: str = 'swish',
               gating_activation: str = 'sigmoid',
               use_sync_bn: bool = True,
               norm_momentum: float = 0.99,
               norm_epsilon: float = 0.001,
               kernel_initializer: str = 'HeNormal',
               kernel_regularizer: Optional[str] = None,
               bias_regularizer: Optional[str] = None,
               stochastic_depth_drop_rate: float = 0.,
               use_external_states: bool = False,
               output_states: bool = True,
               average_pooling_type: str = '3d',
               **kwargs):
    """MoViNet initialization function.

    Args:
      model_id: name of MoViNet backbone model.
      causal: use causal mode, with CausalConv and CausalSE operations.
      use_positional_encoding:  if True, adds a positional encoding before
          temporal convolutions and the cumulative global average pooling
          layers.
      conv_type: '3d', '2plus1d', or '3d_2plus1d'. '3d' configures the network
        to use the default 3D convolution. '2plus1d' uses (2+1)D convolution
        with Conv2D operations and 2D reshaping (e.g., a 5x3x3 kernel becomes
        3x3 followed by 5x1 conv). '3d_2plus1d' uses (2+1)D convolution with
        Conv3D and no 2D reshaping (e.g., a 5x3x3 kernel becomes 1x3x3 followed
        by 5x1x1 conv).
      se_type: '3d', '2d', '2plus3d' or 'none'. '3d' uses the default 3D
          spatiotemporal global average pooling for squeeze excitation. '2d'
          uses 2D spatial global average pooling  on each frame. '2plus3d'
          concatenates both 3D and 2D global average pooling.
      input_specs: the model input spec to use.
      activation: name of the main activation function.
      gating_activation: gating activation to use in squeeze excitation layers.
      use_sync_bn: if True, use synchronized batch normalization.
      norm_momentum: normalization momentum for the moving average.
      norm_epsilon: small float added to variance to avoid dividing by
        zero.
      kernel_initializer: kernel_initializer for convolutional layers.
      kernel_regularizer: tf_keras.regularizers.Regularizer object for Conv2D.
        Defaults to None.
      bias_regularizer: tf_keras.regularizers.Regularizer object for Conv2d.
        Defaults to None.
      stochastic_depth_drop_rate: the base rate for stochastic depth.
      use_external_states: if True, expects states to be passed as additional
        input.
      output_states: if True, output intermediate states that can be used to run
          the model in streaming mode. Inputting the output states of the
          previous input clip with the current input clip will utilize a stream
          buffer for streaming video.
      average_pooling_type: The average pooling type. Currently supporting
        ['3d', '2d', 'none'].
      **kwargs: keyword arguments to be passed.
    """
    block_specs = BLOCK_SPECS[model_id]
    if input_specs is None:
      input_specs = tf_keras.layers.InputSpec(shape=[None, None, None, None, 3])

    if conv_type not in ('3d', '2plus1d', '3d_2plus1d'):
      raise ValueError('Unknown conv type: {}'.format(conv_type))
    if se_type not in ('3d', '2d', '2plus3d', 'none'):
      raise ValueError('Unknown squeeze excitation type: {}'.format(se_type))

    self._model_id = model_id
    self._block_specs = block_specs
    self._causal = causal
    self._use_positional_encoding = use_positional_encoding
    self._conv_type = conv_type
    self._se_type = se_type
    self._input_specs = input_specs
    self._use_sync_bn = use_sync_bn
    self._activation = activation
    self._gating_activation = gating_activation
    self._norm_momentum = norm_momentum
    self._norm_epsilon = norm_epsilon
    self._norm = tf_keras.layers.BatchNormalization
    self._kernel_initializer = kernel_initializer
    self._kernel_regularizer = kernel_regularizer
    self._bias_regularizer = bias_regularizer
    self._stochastic_depth_drop_rate = stochastic_depth_drop_rate
    self._use_external_states = use_external_states
    self._output_states = output_states
    self._average_pooling_type = average_pooling_type

    if self._use_external_states and not self._causal:
      raise ValueError('External states should be used with causal mode.')
    if not isinstance(block_specs[0], StemSpec):
      raise ValueError(
          'Expected first spec to be StemSpec, got {}'.format(block_specs[0]))
    if not isinstance(block_specs[-1], HeadSpec):
      raise ValueError(
          'Expected final spec to be HeadSpec, got {}'.format(block_specs[-1]))
    self._head_filters = block_specs[-1].head_filters

    state_specs = None
    if use_external_states:
      self._set_dtype_policy(input_specs.dtype)
      state_specs = self.initial_state_specs(input_specs.shape)

    inputs, outputs = self._build_network(input_specs, state_specs=state_specs)

    super(Movinet, self).__init__(inputs=inputs, outputs=outputs, **kwargs)

    self._state_specs = state_specs