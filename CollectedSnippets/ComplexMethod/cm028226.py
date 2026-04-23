def fpn_top_down_feature_maps(image_features,
                              depth,
                              use_depthwise=False,
                              use_explicit_padding=False,
                              use_bounded_activations=False,
                              scope=None,
                              use_native_resize_op=False):
  """Generates `top-down` feature maps for Feature Pyramid Networks.

  See https://arxiv.org/abs/1612.03144 for details.

  Args:
    image_features: list of tuples of (tensor_name, image_feature_tensor).
      Spatial resolutions of succesive tensors must reduce exactly by a factor
      of 2.
    depth: depth of output feature maps.
    use_depthwise: whether to use depthwise separable conv instead of regular
      conv.
    use_explicit_padding: whether to use explicit padding.
    use_bounded_activations: Whether or not to clip activations to range
      [-ACTIVATION_BOUND, ACTIVATION_BOUND]. Bounded activations better lend
      themselves to quantized inference.
    scope: A scope name to wrap this op under.
    use_native_resize_op: If True, uses tf.image.resize_nearest_neighbor op for
      the upsampling process instead of reshape and broadcasting implementation.

  Returns:
    feature_maps: an OrderedDict mapping keys (feature map names) to
      tensors where each tensor has shape [batch, height_i, width_i, depth_i].
  """
  with tf.name_scope(scope, 'top_down'):
    num_levels = len(image_features)
    output_feature_maps_list = []
    output_feature_map_keys = []
    padding = 'VALID' if use_explicit_padding else 'SAME'
    kernel_size = 3
    with slim.arg_scope(
        [slim.conv2d, slim.separable_conv2d], padding=padding, stride=1):
      top_down = slim.conv2d(
          image_features[-1][1],
          depth, [1, 1], activation_fn=None, normalizer_fn=None,
          scope='projection_%d' % num_levels)
      if use_bounded_activations:
        top_down = tf.clip_by_value(top_down, -ACTIVATION_BOUND,
                                    ACTIVATION_BOUND)
      output_feature_maps_list.append(top_down)
      output_feature_map_keys.append(
          'top_down_%s' % image_features[-1][0])

      for level in reversed(list(range(num_levels - 1))):
        if use_native_resize_op:
          with tf.name_scope('nearest_neighbor_upsampling'):
            top_down_shape = shape_utils.combined_static_and_dynamic_shape(
                top_down)
            top_down = tf.image.resize_nearest_neighbor(
                top_down, [top_down_shape[1] * 2, top_down_shape[2] * 2])
        else:
          top_down = ops.nearest_neighbor_upsampling(top_down, scale=2)
        residual = slim.conv2d(
            image_features[level][1], depth, [1, 1],
            activation_fn=None, normalizer_fn=None,
            scope='projection_%d' % (level + 1))
        if use_bounded_activations:
          residual = tf.clip_by_value(residual, -ACTIVATION_BOUND,
                                      ACTIVATION_BOUND)
        if use_explicit_padding:
          # slice top_down to the same shape as residual
          residual_shape = tf.shape(residual)
          top_down = top_down[:, :residual_shape[1], :residual_shape[2], :]
        top_down += residual
        if use_bounded_activations:
          top_down = tf.clip_by_value(top_down, -ACTIVATION_BOUND,
                                      ACTIVATION_BOUND)
        if use_depthwise:
          conv_op = functools.partial(slim.separable_conv2d, depth_multiplier=1)
        else:
          conv_op = slim.conv2d
        pre_output = top_down
        if use_explicit_padding:
          pre_output = ops.fixed_padding(pre_output, kernel_size)
        output_feature_maps_list.append(conv_op(
            pre_output,
            depth, [kernel_size, kernel_size],
            scope='smoothing_%d' % (level + 1)))
        output_feature_map_keys.append('top_down_%s' % image_features[level][0])
      return collections.OrderedDict(reversed(
          list(zip(output_feature_map_keys, output_feature_maps_list))))