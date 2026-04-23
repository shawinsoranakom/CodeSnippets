def xception_module(inputs,
                    depth_list,
                    skip_connection_type,
                    stride,
                    kernel_size=3,
                    unit_rate_list=None,
                    rate=1,
                    activation_fn_in_separable_conv=False,
                    regularize_depthwise=False,
                    outputs_collections=None,
                    scope=None,
                    use_bounded_activation=False,
                    use_explicit_padding=True,
                    use_squeeze_excite=False,
                    se_pool_size=None):
  """An Xception module.

  The output of one Xception module is equal to the sum of `residual` and
  `shortcut`, where `residual` is the feature computed by three separable
  convolution. The `shortcut` is the feature computed by 1x1 convolution with
  or without striding. In some cases, the `shortcut` path could be a simple
  identity function or none (i.e, no shortcut).

  Note that we replace the max pooling operations in the Xception module with
  another separable convolution with striding, since atrous rate is not properly
  supported in current TensorFlow max pooling implementation.

  Args:
    inputs: A tensor of size [batch, height, width, channels].
    depth_list: A list of three integers specifying the depth values of one
      Xception module.
    skip_connection_type: Skip connection type for the residual path. Only
      supports 'conv', 'sum', or 'none'.
    stride: The block unit's stride. Determines the amount of downsampling of
      the units output compared to its input.
    kernel_size: Integer, convolution kernel size.
    unit_rate_list: A list of three integers, determining the unit rate for
      each separable convolution in the xception module.
    rate: An integer, rate for atrous convolution.
    activation_fn_in_separable_conv: Includes activation function in the
      separable convolution or not.
    regularize_depthwise: Whether or not apply L2-norm regularization on the
      depthwise convolution weights.
    outputs_collections: Collection to add the Xception unit output.
    scope: Optional variable_scope.
    use_bounded_activation: Whether or not to use bounded activations. Bounded
      activations better lend themselves to quantized inference.
    use_explicit_padding: If True, use explicit padding to make the model fully
      compatible with the open source version, otherwise use the native
      Tensorflow 'SAME' padding.
    use_squeeze_excite: Boolean, use squeeze-and-excitation or not.
    se_pool_size: None or integer specifying the pooling size used in SE module.

  Returns:
    The Xception module's output.

  Raises:
    ValueError: If depth_list and unit_rate_list do not contain three elements,
      or if stride != 1 for the third separable convolution operation in the
      residual path, or unsupported skip connection type.
  """
  if len(depth_list) != 3:
    raise ValueError('Expect three elements in depth_list.')
  if unit_rate_list:
    if len(unit_rate_list) != 3:
      raise ValueError('Expect three elements in unit_rate_list.')

  with tf.variable_scope(scope, 'xception_module', [inputs]) as sc:
    residual = inputs

    def _separable_conv(features, depth, kernel_size, depth_multiplier,
                        regularize_depthwise, rate, stride, scope):
      """Separable conv block."""
      if activation_fn_in_separable_conv:
        activation_fn = tf.nn.relu6 if use_bounded_activation else tf.nn.relu
      else:
        if use_bounded_activation:
          # When use_bounded_activation is True, we clip the feature values and
          # apply relu6 for activation.
          activation_fn = lambda x: tf.clip_by_value(x, -_CLIP_CAP, _CLIP_CAP)
          features = tf.nn.relu6(features)
        else:
          # Original network design.
          activation_fn = None
          features = tf.nn.relu(features)
      return separable_conv2d_same(features,
                                   depth,
                                   kernel_size,
                                   depth_multiplier=depth_multiplier,
                                   stride=stride,
                                   rate=rate,
                                   activation_fn=activation_fn,
                                   use_explicit_padding=use_explicit_padding,
                                   regularize_depthwise=regularize_depthwise,
                                   scope=scope)
    for i in range(3):
      residual = _separable_conv(residual,
                                 depth_list[i],
                                 kernel_size=kernel_size,
                                 depth_multiplier=1,
                                 regularize_depthwise=regularize_depthwise,
                                 rate=rate*unit_rate_list[i],
                                 stride=stride if i == 2 else 1,
                                 scope='separable_conv' + str(i+1))
    if use_squeeze_excite:
      residual = mobilenet_v3_ops.squeeze_excite(
          input_tensor=residual,
          squeeze_factor=16,
          inner_activation_fn=tf.nn.relu,
          gating_fn=lambda x: tf.nn.relu6(x+3)*0.16667,
          pool=se_pool_size)

    if skip_connection_type == 'conv':
      shortcut = slim.conv2d(inputs,
                             depth_list[-1],
                             [1, 1],
                             stride=stride,
                             activation_fn=None,
                             scope='shortcut')
      if use_bounded_activation:
        residual = tf.clip_by_value(residual, -_CLIP_CAP, _CLIP_CAP)
        shortcut = tf.clip_by_value(shortcut, -_CLIP_CAP, _CLIP_CAP)
      outputs = residual + shortcut
      if use_bounded_activation:
        outputs = tf.nn.relu6(outputs)
    elif skip_connection_type == 'sum':
      if use_bounded_activation:
        residual = tf.clip_by_value(residual, -_CLIP_CAP, _CLIP_CAP)
        inputs = tf.clip_by_value(inputs, -_CLIP_CAP, _CLIP_CAP)
      outputs = residual + inputs
      if use_bounded_activation:
        outputs = tf.nn.relu6(outputs)
    elif skip_connection_type == 'none':
      outputs = residual
    else:
      raise ValueError('Unsupported skip connection type.')

    return slim.utils.collect_named_outputs(outputs_collections,
                                            sc.name,
                                            outputs)