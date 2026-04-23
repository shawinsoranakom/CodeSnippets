def _mobilenet_base(
      self, inputs: tf.Tensor
  ) -> tuple[tf.Tensor, dict[str, tf.Tensor], int]:
    """Builds the base MobileNet architecture.

    Args:
      inputs: A `tf.Tensor` of shape `[batch_size, height, width, channels]`.

    Returns:
      A tuple of output Tensor and dictionary that collects endpoints.
    """

    input_shape = inputs.get_shape().as_list()
    if len(input_shape) != 4:
      raise ValueError('Expected rank 4 input, was: %d' % len(input_shape))

    # The current_stride variable keeps track of the output stride of the
    # activations, i.e., the running product of convolution strides up to the
    # current network layer. This allows us to invoke atrous convolution
    # whenever applying the next convolution would result in the activations
    # having output stride larger than the target output_stride.
    current_stride = 1

    # The atrous convolution rate parameter.
    rate = 1

    # Used to calulate stochastic depth drop rate. Some blocks do not use
    # stochastic depth since they do not have residuals. For simplicity, we
    # count here all the blocks in the model. If one or more of the last layers
    # do not use stochastic depth, it can be compensated with larger stochastic
    # depth drop rate.
    num_blocks = len(self._decoded_specs)

    net = inputs
    endpoints = {}
    endpoint_level = 2
    for block_idx, block_def in enumerate(self._decoded_specs):
      block_name = 'block_group_{}_{}'.format(block_def.block_fn, block_idx)
      # A small catch for gpooling block with None strides
      if not block_def.strides:
        block_def.strides = 1
      if (self._output_stride is not None and
          current_stride == self._output_stride):
        # If we have reached the target output_stride, then we need to employ
        # atrous convolution with stride=1 and multiply the atrous rate by the
        # current unit's stride for use in subsequent layers.
        layer_stride = 1
        layer_rate = rate
        rate *= block_def.strides
      else:
        layer_stride = block_def.strides
        layer_rate = 1
        current_stride *= block_def.strides

      if self._flat_stochastic_depth_drop_rate:
        stochastic_depth_drop_rate = self._stochastic_depth_drop_rate
      else:
        stochastic_depth_drop_rate = nn_layers.get_stochastic_depth_rate(
            self._stochastic_depth_drop_rate, block_idx + 1, num_blocks
        )
      if stochastic_depth_drop_rate is not None:
        logging.info(
            'stochastic_depth_drop_rate: %f for block = %d',
            stochastic_depth_drop_rate,
            block_idx,
        )

      intermediate_endpoints = {}
      if block_def.block_fn == 'convbn':

        net = Conv2DBNBlock(
            filters=block_def.filters,
            kernel_size=block_def.kernel_size,
            strides=block_def.strides,
            activation=block_def.activation,
            use_bias=block_def.use_bias,
            use_normalization=block_def.use_normalization,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            bias_regularizer=self._bias_regularizer,
            use_sync_bn=self._use_sync_bn,
            norm_momentum=self._norm_momentum,
            norm_epsilon=self._norm_epsilon
        )(net)

      elif block_def.block_fn == 'depsepconv':
        net = nn_blocks.DepthwiseSeparableConvBlock(
            filters=block_def.filters,
            kernel_size=block_def.kernel_size,
            strides=layer_stride,
            activation=block_def.activation,
            dilation_rate=layer_rate,
            regularize_depthwise=self._regularize_depthwise,
            kernel_initializer=self._kernel_initializer,
            kernel_regularizer=self._kernel_regularizer,
            use_sync_bn=self._use_sync_bn,
            norm_momentum=self._norm_momentum,
            norm_epsilon=self._norm_epsilon,
        )(net)

      elif block_def.block_fn == 'mhsa':
        block = nn_blocks.MultiHeadSelfAttentionBlock(
            input_dim=block_def.filters,
            num_heads=block_def.num_heads,
            key_dim=block_def.key_dim,
            value_dim=block_def.value_dim,
            use_multi_query=block_def.use_multi_query,
            query_h_strides=block_def.query_h_strides,
            query_w_strides=block_def.query_w_strides,
            kv_strides=block_def.kv_strides,
            downsampling_dw_kernel_size=block_def.downsampling_dw_kernel_size,
            cpe_dw_kernel_size=block_def.kernel_size,
            stochastic_depth_drop_rate=self._stochastic_depth_drop_rate,
            use_sync_bn=self._use_sync_bn,
            use_residual=block_def.use_residual,
            norm_momentum=self._norm_momentum,
            norm_epsilon=self._norm_epsilon,
            use_layer_scale=block_def.use_layer_scale,
            output_intermediate_endpoints=self._output_intermediate_endpoints,
        )
        if self._output_intermediate_endpoints:
          net, intermediate_endpoints = block(net)
        else:
          net = block(net)

      elif block_def.block_fn in (
          'invertedbottleneck',
          'fused_ib',
          'uib',
      ):
        use_rate = rate
        if layer_rate > 1 and block_def.kernel_size != 1:
          # We will apply atrous rate in the following cases:
          # 1) When kernel_size is not in params, the operation then uses
          #   default kernel size 3x3.
          # 2) When kernel_size is in params, and if the kernel_size is not
          #   equal to (1, 1) (there is no need to apply atrous convolution to
          #   any 1x1 convolution).
          use_rate = layer_rate
        in_filters = net.shape.as_list()[-1]
        args = {
            'in_filters': in_filters,
            'out_filters': block_def.filters,
            'strides': layer_stride,
            'expand_ratio': block_def.expand_ratio,
            'activation': block_def.activation,
            'use_residual': block_def.use_residual,
            'dilation_rate': use_rate,
            'regularize_depthwise': self._regularize_depthwise,
            'kernel_initializer': self._kernel_initializer,
            'kernel_regularizer': self._kernel_regularizer,
            'bias_regularizer': self._bias_regularizer,
            'use_sync_bn': self._use_sync_bn,
            'norm_momentum': self._norm_momentum,
            'norm_epsilon': self._norm_epsilon,
            'stochastic_depth_drop_rate': stochastic_depth_drop_rate,
            'divisible_by': self._get_divisible_by(),
            'output_intermediate_endpoints': (
                self._output_intermediate_endpoints
            ),
        }
        if block_def.block_fn in ('invertedbottleneck', 'fused_ib'):
          args.update({
              'kernel_size': block_def.kernel_size,
              'se_ratio': block_def.se_ratio,
              'expand_se_in_filters': True,
              'use_depthwise': (
                  block_def.use_depthwise
                  if block_def.block_fn == 'invertedbottleneck'
                  else False
              ),
              'se_gating_activation': 'hard_sigmoid',
          })
          block = nn_blocks.InvertedBottleneckBlock(**args)
        else:
          args.update({
              'middle_dw_downsample': block_def.middle_dw_downsample,
              'start_dw_kernel_size': block_def.start_dw_kernel_size,
              'middle_dw_kernel_size': block_def.middle_dw_kernel_size,
              'end_dw_kernel_size': block_def.end_dw_kernel_size,
              'use_layer_scale': block_def.use_layer_scale,
          })
          block = nn_blocks.UniversalInvertedBottleneckBlock(**args)

        if self._output_intermediate_endpoints:
          net, intermediate_endpoints = block(net)
        else:
          net = block(net)

      elif block_def.block_fn == 'gpooling':
        net = layers.GlobalAveragePooling2D(keepdims=True)(net)

      else:
        raise ValueError(
            'Unknown block type {} for layer {}'.format(
                block_def.block_fn, block_idx
            )
        )

      net = tf_keras.layers.Activation('linear', name=block_name)(net)

      if block_def.is_output:
        endpoints[str(endpoint_level)] = net
        for key, tensor in intermediate_endpoints.items():
          endpoints[str(endpoint_level) + '/' + key] = tensor
        if current_stride != self._output_stride:
          endpoint_level += 1

    if str(endpoint_level) in endpoints:
      endpoint_level += 1
    return net, endpoints, endpoint_level