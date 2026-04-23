def build(self, input_shape):
    # Starting depthwise conv.
    if self._start_dw_kernel_size:
      self._start_dw_conv = helper.DepthwiseConv2DQuantized(
          kernel_size=self._start_dw_kernel_size,
          strides=self._strides if not self._middle_dw_downsample else 1,
          padding='same',
          depth_multiplier=1,
          dilation_rate=self._dilation_rate,
          use_bias=False,
          depthwise_initializer=tf_utils.clone_initializer(
              self._kernel_initializer
          ),
          depthwise_regularizer=self._depthwise_regularizer,
          bias_regularizer=self._bias_regularizer,
      )
      # No activation -> quantized norm should be okay.
      self._start_dw_norm = self._norm_with_quantize(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon,
      )

    # Expansion with 1x1 convs.
    expand_filters = nn_layers.make_divisible(
        self._in_filters * self._expand_ratio, self._divisible_by
    )

    self._expand_conv = helper.Conv2DQuantized(
        filters=expand_filters,
        kernel_size=1,
        strides=1,
        padding='same',
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
    )
    self._expand_norm = helper.norm_by_activation(
        self._activation, self._norm_with_quantize, self._norm
    )(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon,
    )
    self._expand_act = tfmot.quantization.keras.QuantizeWrapperV2(
        tf_utils.get_activation(self._activation, use_keras_layer=True),
        configs.Default8BitActivationQuantizeConfig(),
    )

    # Middle depthwise conv.
    if self._middle_dw_kernel_size:
      self._middle_dw_conv = helper.DepthwiseConv2DQuantized(
          kernel_size=self._middle_dw_kernel_size,
          strides=self._strides if self._middle_dw_downsample else 1,
          padding='same',
          depth_multiplier=1,
          dilation_rate=self._dilation_rate,
          use_bias=False,
          depthwise_initializer=tf_utils.clone_initializer(
              self._kernel_initializer
          ),
          depthwise_regularizer=self._depthwise_regularizer,
          bias_regularizer=self._bias_regularizer,
      )
      self._middle_dw_norm = helper.norm_by_activation(
          self._activation, self._norm_with_quantize, self._norm
      )(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon,
      )
      self._middle_dw_act = tfmot.quantization.keras.QuantizeWrapperV2(
          tf_utils.get_activation(
              self._depthwise_activation, use_keras_layer=True
          ),
          configs.Default8BitActivationQuantizeConfig(),
      )

    # Projection with 1x1 convs.
    self._proj_conv = helper.Conv2DQuantized(
        filters=self._out_filters,
        kernel_size=1,
        strides=1,
        padding='same',
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
    )
    # No activation -> quantized norm should be okay.
    self._proj_norm = self._norm_with_quantize(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon,
    )

    # Ending depthwise conv.
    if self._end_dw_kernel_size:
      self._end_dw_conv = helper.DepthwiseConv2DQuantized(
          kernel_size=self._end_dw_kernel_size,
          strides=1,
          padding='same',
          depth_multiplier=1,
          dilation_rate=self._dilation_rate,
          use_bias=False,
          depthwise_initializer=tf_utils.clone_initializer(
              self._kernel_initializer
          ),
          depthwise_regularizer=self._depthwise_regularizer,
          bias_regularizer=self._bias_regularizer,
      )
      self._end_dw_norm = self._norm_with_quantize(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon,
      )

    if self._use_layer_scale:
      raise NotImplementedError

    if self._stochastic_depth_drop_rate:
      self._stochastic_depth = nn_layers.StochasticDepth(
          self._stochastic_depth_drop_rate
      )
    else:
      self._stochastic_depth = None

    super().build(input_shape)