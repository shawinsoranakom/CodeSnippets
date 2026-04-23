def build(self, input_shape):
    # First 1x1 conv for channel expansion.
    expand_filters = nn_layers.make_divisible(
        self._in_filters * self._expand_ratio, self._divisible_by
    )

    expand_kernel = 1 if self._use_depthwise else self._kernel_size
    expand_stride = 1 if self._use_depthwise else self._strides

    self._conv0 = tf_keras.layers.Conv2D(
        filters=expand_filters,
        kernel_size=expand_kernel,
        strides=expand_stride,
        padding='same',
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
    )
    self._norm0 = self._norm(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon,
        synchronized=self._use_sync_bn,
    )
    self._activation_layer = tf_utils.get_activation(
        self._activation, use_keras_layer=True
    )

    if self._use_depthwise:
      # Depthwise conv.
      self._conv1 = tf_keras.layers.DepthwiseConv2D(
          kernel_size=(self._kernel_size, self._kernel_size),
          strides=self._strides,
          padding='same',
          depth_multiplier=1,
          dilation_rate=self._dilation_rate,
          use_bias=False,
          depthwise_initializer=tf_utils.clone_initializer(
              self._kernel_initializer),
          depthwise_regularizer=self._depthsize_regularizer,
          bias_regularizer=self._bias_regularizer)
      self._norm1 = self._norm(
          axis=self._bn_axis,
          momentum=self._norm_momentum,
          epsilon=self._norm_epsilon,
          synchronized=self._use_sync_bn,
      )
      self._depthwise_activation_layer = tf_utils.get_activation(
          self._depthwise_activation, use_keras_layer=True)

    # Squeeze and excitation.
    if self._se_ratio and self._se_ratio > 0 and self._se_ratio <= 1:
      logging.info('Use Squeeze and excitation.')
      in_filters = self._in_filters
      if self._expand_se_in_filters:
        in_filters = expand_filters
      self._squeeze_excitation = nn_layers.SqueezeExcitation(
          in_filters=in_filters,
          out_filters=expand_filters,
          se_ratio=self._se_ratio,
          divisible_by=self._divisible_by,
          round_down_protect=self._se_round_down_protect,
          kernel_initializer=tf_utils.clone_initializer(
              self._kernel_initializer),
          kernel_regularizer=self._kernel_regularizer,
          bias_regularizer=self._bias_regularizer,
          activation=self._se_inner_activation,
          gating_activation=self._se_gating_activation)
    else:
      self._squeeze_excitation = None

    # Last 1x1 conv.
    self._conv2 = tf_keras.layers.Conv2D(
        filters=self._out_filters,
        kernel_size=1,
        strides=1,
        padding='same',
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer)
    self._norm2 = self._norm(
        axis=self._bn_axis,
        momentum=self._norm_momentum,
        epsilon=self._norm_epsilon,
        synchronized=self._use_sync_bn,
    )

    if self._stochastic_depth_drop_rate:
      self._stochastic_depth = nn_layers.StochasticDepth(
          self._stochastic_depth_drop_rate)
    else:
      self._stochastic_depth = None
    self._add = tf_keras.layers.Add()

    super(InvertedBottleneckBlock, self).build(input_shape)