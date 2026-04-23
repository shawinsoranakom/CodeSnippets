def _mnasfpn_cell(feature_maps,
                  feature_levels,
                  cell_spec,
                  output_channel=48,
                  use_explicit_padding=False,
                  use_native_resize_op=False,
                  multiplier_func=None):
  """Create a MnasFPN cell.

  Args:
    feature_maps: input feature maps.
    feature_levels: levels of the feature maps.
    cell_spec: A list of Block configs.
    output_channel: Number of features for the input, output and intermediate
      feature maps.
    use_explicit_padding: Whether to use explicit padding.
    use_native_resize_op: Whether to use native resize op.
    multiplier_func: Depth-multiplier function. If None, use identity function.

  Returns:
    A transformed list of feature maps at the same resolutions as the inputs.
  """
  # This is the level where multipliers are realized.
  if multiplier_func is None:
    multiplier_func = lambda x: x
  num_outputs = len(feature_maps)
  cell_features = list(feature_maps)
  cell_levels = list(feature_levels)
  padding = 'VALID' if use_explicit_padding else 'SAME'
  for bi, block in enumerate(cell_spec):
    with tf.variable_scope('block_{}'.format(bi)):
      block_level = block.output_level
      intermediate_feature = None
      for i, inp in enumerate(block.inputs):
        with tf.variable_scope('input_{}'.format(i)):
          input_level = cell_levels[inp]
          node = _apply_size_dependent_ordering(
              cell_features[inp], input_level, block_level,
              multiplier_func(block.expansion_size), use_explicit_padding,
              use_native_resize_op)
        # Add features incrementally to avoid producing AddN, which doesn't
        # play well with TfLite.
        if intermediate_feature is None:
          intermediate_feature = node
        else:
          intermediate_feature += node
      node = tf.nn.relu6(intermediate_feature)
      node = slim.separable_conv2d(
          _maybe_pad(node, use_explicit_padding, block.kernel_size),
          multiplier_func(output_channel),
          block.kernel_size,
          activation_fn=None,
          normalizer_fn=slim.batch_norm,
          padding=padding,
          scope='SepConv')
    cell_features.append(node)
    cell_levels.append(block_level)

  # Cell-wide residuals.
  out_idx = range(len(cell_features) - num_outputs, len(cell_features))
  for in_i, out_i in enumerate(out_idx):
    if cell_features[out_i].shape.as_list(
    ) == cell_features[in_i].shape.as_list():
      cell_features[out_i] += cell_features[in_i]

  return cell_features[-num_outputs:]