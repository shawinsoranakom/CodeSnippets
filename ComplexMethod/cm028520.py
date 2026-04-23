def build(self, input_shape: tf.TensorShape) -> None:
    """Builds block according to the arguments."""

    channel_axis = 3 if self._data_format == 'channels_last' else 1
    input_size = input_shape[channel_axis]
    inner_size = self._hidden_size * self._expansion_rate

    norm_cls = _config_batch_norm(
        self._norm_type,
        bn_momentum=self._bn_momentum,
        bn_epsilon=self._bn_epsilon,
    )

    # Shortcut projection.
    if input_size != self._hidden_size:
      self._shortcut_conv = tf_keras.layers.Conv2D(
          filters=self._hidden_size,
          kernel_size=1,
          strides=1,
          padding='same',
          data_format=self._data_format,
          kernel_initializer=self._kernel_initializer,
          bias_initializer=self._bias_initializer,
          use_bias=True,
          name='shortcut_conv',
      )
    else:
      self._shortcut_conv = None

    # Pre-Activation norm
    self._pre_norm = norm_cls(name='pre_norm')

    # Expansion phase. Called if not using fused convolutions and expansion
    # phase is necessary.
    if self._expansion_rate != 1:
      self._expand_conv = tf_keras.layers.Conv2D(
          filters=inner_size,
          kernel_size=1,
          strides=(
              self._pool_stride if self._downsample_loc == 'expand_conv' else 1
          ),
          kernel_initializer=self._kernel_initializer,
          padding='same',
          data_format=self._data_format,
          use_bias=False,
          name='expand_conv',
      )
      self._expand_norm = norm_cls(name='expand_norm')

    # Depth-wise convolution phase. Called if not using fused convolutions.
    self._depthwise_conv = tf_keras.layers.DepthwiseConv2D(
        kernel_size=self._kernel_size,
        strides=(
            self._pool_stride if self._downsample_loc == 'depth_conv' else 1
        ),
        depthwise_initializer=self._kernel_initializer,
        padding='same',
        data_format=self._data_format,
        use_bias=False,
        name='depthwise_conv',
    )
    self._depthwise_norm = norm_cls(name='depthwise_norm')

    if self._se_ratio is not None and 0 < self._se_ratio <= 1:
      se_filters = max(1, int(self._hidden_size * self._se_ratio))
      self._se = SqueezeAndExcitation(
          se_filters=se_filters,
          output_filters=inner_size,
          data_format=self._data_format,
          kernel_initializer=self._kernel_initializer,
          bias_initializer=self._bias_initializer,
          name='se',
      )
    else:
      self._se = None

    # Output phase.
    self._shrink_conv = tf_keras.layers.Conv2D(
        filters=self._hidden_size,
        kernel_size=1,
        strides=1,
        padding='same',
        data_format=self._data_format,
        kernel_initializer=self._kernel_initializer,
        bias_initializer=self._bias_initializer,
        use_bias=True,
        name='shrink_conv',
    )