def build(self, input_shape: Optional[Union[Sequence[int], tf.Tensor]]):
    """Build variables and child layers to prepare for calling."""
    conv2d_quantized = _quantize_wrapped_layer(
        tf_keras.layers.Conv2D,
        configs.DefaultNBitConvQuantizeConfig(
            ['kernel'], ['activation'], False,
            num_bits_weight=self._num_bits_weight,
            num_bits_activation=self._num_bits_activation))
    depthwise_conv2d_quantized = _quantize_wrapped_layer(
        tf_keras.layers.DepthwiseConv2D,
        configs.DefaultNBitConvQuantizeConfig(
            ['depthwise_kernel'], ['activation'], False,
            num_bits_weight=self._num_bits_weight,
            num_bits_activation=self._num_bits_activation))
    expand_filters = self._in_filters
    if self._expand_ratio > 1:
      # First 1x1 conv for channel expansion.
      expand_filters = nn_layers.make_divisible(
          self._in_filters * self._expand_ratio, self._divisible_by)

      expand_kernel = 1 if self._use_depthwise else self._kernel_size
      expand_stride = 1 if self._use_depthwise else self._strides

      self._conv0 = conv2d_quantized(
          filters=expand_filters,
          kernel_size=expand_kernel,
          strides=expand_stride,
          padding='same',
          use_bias=False,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer,
          activation=NoOpActivation())
      self._norm0 = self._norm_with_quantize(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon)
      self._activation_layer = tfmot.quantization.keras.QuantizeWrapperV2(
          tf_utils.get_activation(self._activation, use_keras_layer=True),
          configs.DefaultNBitActivationQuantizeConfig(
              num_bits_weight=self._num_bits_weight,
              num_bits_activation=self._num_bits_activation))

    if self._use_depthwise:
      # Depthwise conv.
      self._conv1 = depthwise_conv2d_quantized(
          kernel_size=(self._kernel_size, self._kernel_size),
          strides=self._strides,
          padding='same',
          depth_multiplier=1,
          dilation_rate=self._dilation_rate,
          use_bias=False,
          depthwise_initializer=self._kernel_initializer,
          depthwise_regularizer=self._depthsize_regularizer,
          bias_regularizer=self._bias_regularizer,
          activation=NoOpActivation())
      self._norm1 = self._norm_with_quantize(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon)
      self._depthwise_activation_layer = (
          tfmot.quantization.keras.QuantizeWrapperV2(
              tf_utils.get_activation(self._depthwise_activation,
                                      use_keras_layer=True),
              configs.DefaultNBitActivationQuantizeConfig(
                  num_bits_weight=self._num_bits_weight,
                  num_bits_activation=self._num_bits_activation)))

    # Squeeze and excitation.
    if self._se_ratio and self._se_ratio > 0 and self._se_ratio <= 1:
      logging.info('Use Squeeze and excitation.')
      in_filters = self._in_filters
      if self._expand_se_in_filters:
        in_filters = expand_filters
      self._squeeze_excitation = qat_nn_layers.SqueezeExcitationNBitQuantized(
          in_filters=in_filters,
          out_filters=expand_filters,
          se_ratio=self._se_ratio,
          divisible_by=self._divisible_by,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer,
          activation=self._se_inner_activation,
          gating_activation=self._se_gating_activation,
          num_bits_weight=self._num_bits_weight,
          num_bits_activation=self._num_bits_activation)
    else:
      self._squeeze_excitation = None

    # Last 1x1 conv.
    self._conv2 = conv2d_quantized(
        filters=self._out_filters,
        kernel_size=1,
        strides=1,
        padding='same',
        use_bias=False,
        kernel_initializer=self._kernel_initializer,
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
        activation=NoOpActivation())
    self._norm2 = self._norm_with_quantize(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon)

    if self._stochastic_depth_drop_rate:
      self._stochastic_depth = nn_layers.StochasticDepth(
          self._stochastic_depth_drop_rate)
    else:
      self._stochastic_depth = None
    self._add = tf_keras.layers.Add()

    super().build(input_shape)