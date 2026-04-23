def build(self, input_shape):
    """Builds the layer with the given input shape."""
    padding = 'causal' if self._causal else 'same'
    self._groups = input_shape[-1] if self._depthwise else 1

    self._batch_norm = None
    self._batch_norm_temporal = None
    if self._use_batch_norm:
      self._batch_norm = self._batch_norm_layer(
          momentum=self._batch_norm_momentum,
          epsilon=self._batch_norm_epsilon,
          synchronized=self._use_sync_bn,
          name='bn')
      if self._conv_type != '3d' and self._kernel_size[0] > 1:
        self._batch_norm_temporal = self._batch_norm_layer(
            momentum=self._batch_norm_momentum,
            epsilon=self._batch_norm_epsilon,
            synchronized=self._use_sync_bn,
            name='bn_temporal')

    self._conv_temporal = None
    if self._conv_type == '3d_2plus1d' and self._kernel_size[0] > 1:
      self._conv = nn_layers.Conv3D(
          self._filters,
          (1, self._kernel_size[1], self._kernel_size[2]),
          strides=(1, self._strides[1], self._strides[2]),
          padding='same',
          groups=self._groups,
          use_bias=self._use_bias,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          use_buffered_input=False,
          name='conv3d')
      self._conv_temporal = nn_layers.Conv3D(
          self._filters,
          (self._kernel_size[0], 1, 1),
          strides=(self._strides[0], 1, 1),
          padding=padding,
          groups=self._groups,
          use_bias=self._use_bias,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          use_buffered_input=self._use_buffered_input,
          name='conv3d_temporal')
    elif self._conv_type == '2plus1d':
      self._conv = MobileConv2D(
          self._filters,
          (self._kernel_size[1], self._kernel_size[2]),
          strides=(self._strides[1], self._strides[2]),
          padding='same',
          use_depthwise=self._depthwise,
          groups=self._groups,
          use_bias=self._use_bias,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          use_buffered_input=False,
          batch_norm_op=self._batch_norm,
          activation_op=self._activation_layer,
          name='conv2d')
      if self._kernel_size[0] > 1:
        self._conv_temporal = MobileConv2D(
            self._filters,
            (self._kernel_size[0], 1),
            strides=(self._strides[0], 1),
            padding=padding,
            use_temporal=True,
            use_depthwise=self._depthwise,
            groups=self._groups,
            use_bias=self._use_bias,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            use_buffered_input=self._use_buffered_input,
            batch_norm_op=self._batch_norm_temporal,
            activation_op=self._activation_layer,
            name='conv2d_temporal')
    else:
      self._conv = nn_layers.Conv3D(
          self._filters,
          self._kernel_size,
          strides=self._strides,
          padding=padding,
          groups=self._groups,
          use_bias=self._use_bias,
          kernel_initializer=self._kernel_initializer,
          kernel_regularizer=self._kernel_regularizer,
          use_buffered_input=self._use_buffered_input,
          name='conv3d')

    super(ConvBlock, self).build(input_shape)