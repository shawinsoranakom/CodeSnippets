def build(
      self, input_shape: Union[tf.TensorShape, Dict[str,
                                                    tf.TensorShape]]) -> None:
    """Builds this MOSAIC encoder block with the given single input shape."""
    input_shape = (
        input_shape[self._encoder_input_level]
        if isinstance(input_shape, dict) else input_shape)
    self._data_format = tf_keras.backend.image_data_format()
    if self._data_format == 'channels_last':
      height = input_shape[1]
      width = input_shape[2]
    else:
      height = input_shape[2]
      width = input_shape[3]

    self._global_pool_branch = None
    self._spatial_pyramid = []

    for pyramid_pool_bin_num in self._pyramid_pool_bin_nums:
      if pyramid_pool_bin_num == 1:
        global_pool = tf_keras.layers.GlobalAveragePooling2D(
            data_format=self._data_format, keepdims=True)
        global_projection = tf_keras.layers.Conv2D(
            filters=max(self._branch_filter_depths),
            kernel_size=(1, 1),
            padding='same',
            activation=None,
            kernel_regularizer=self._kernel_regularizer,
            kernel_initializer=self._kernel_initializer,
            use_bias=False)
        batch_norm_global_branch = self._bn_op(
            axis=self._bn_axis,
            momentum=self._batchnorm_momentum,
            epsilon=self._batchnorm_epsilon)
        # Use list manually instead of tf_keras.Sequential([])
        self._global_pool_branch = [
            global_pool,
            global_projection,
            batch_norm_global_branch,
        ]
      else:
        if height < pyramid_pool_bin_num or width < pyramid_pool_bin_num:
          raise ValueError('The number of pooling bins must be smaller than '
                           'input sizes.')
        assert pyramid_pool_bin_num >= 2, (
            'Except for the gloabl pooling, the number of bins in pyramid '
            'pooling must be at least two.')
        pool_height, stride_height = self._get_bin_pool_kernel_and_stride(
            height, pyramid_pool_bin_num)
        pool_width, stride_width = self._get_bin_pool_kernel_and_stride(
            width, pyramid_pool_bin_num)
        bin_pool_level = tf_keras.layers.AveragePooling2D(
            pool_size=(pool_height, pool_width),
            strides=(stride_height, stride_width),
            padding='valid',
            data_format=self._data_format)
        self._spatial_pyramid.append(bin_pool_level)

    # Grouped multi-kernel Convolution.
    self._multi_kernel_group_conv = MultiKernelGroupConvBlock(
        output_filter_depths=self._branch_filter_depths,
        kernel_sizes=self._conv_kernel_sizes,
        use_sync_bn=self._use_sync_bn,
        batchnorm_momentum=self._batchnorm_momentum,
        batchnorm_epsilon=self._batchnorm_epsilon,
        activation=self._activation,
        kernel_initializer=self._kernel_initializer,
        kernel_regularizer=self._kernel_regularizer,
        use_depthwise_convolution=self._use_depthwise_convolution)

    # Encoder's final 1x1 feature projection.
    # Considering the relatively large #channels merged before projection,
    # enlarge the projection #channels to the sum of the filter depths of
    # branches.
    self._output_channels = sum(self._branch_filter_depths)
    # Use list manually instead of tf_keras.Sequential([]).
    self._encoder_projection = [
        tf_keras.layers.Conv2D(
            filters=self._output_channels,
            kernel_size=(1, 1),
            padding='same',
            activation=None,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            use_bias=False),
        self._bn_op(
            axis=self._bn_axis,
            momentum=self._batchnorm_momentum,
            epsilon=self._batchnorm_epsilon),
    ]
    # Use the TF2 default feature alignment rule for bilinear resizing.
    self._upsample = tf_keras.layers.Resizing(
        height,
        width,
        interpolation=self._interpolation,
        crop_to_aspect_ratio=False)
    self._concat_layer = tf_keras.layers.Concatenate(axis=self._channel_axis)