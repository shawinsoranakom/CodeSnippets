def _apply_conv_operation(self, net, operation,
                            stride, is_from_original_input, current_step):
    """Applies the predicted conv operation to net."""
    # Dont stride if this is not one of the original hiddenstates
    if stride > 1 and not is_from_original_input:
      stride = 1
    input_filters = get_channel_dim(net.shape)
    filter_size = self._filter_size
    if 'separable' in operation:
      net = _stacked_separable_conv(net, stride, operation, filter_size,
                                    self._use_bounded_activation)
      if self._use_bounded_activation:
        net = tf.clip_by_value(net, -CLIP_BY_VALUE_CAP, CLIP_BY_VALUE_CAP)
    elif operation in ['none']:
      if self._use_bounded_activation:
        net = tf.nn.relu6(net)
      # Check if a stride is needed, then use a strided 1x1 here
      if stride > 1 or (input_filters != filter_size):
        if not self._use_bounded_activation:
          net = tf.nn.relu(net)
        net = slim.conv2d(net, filter_size, 1, stride=stride, scope='1x1')
        net = slim.batch_norm(net, scope='bn_1')
        if self._use_bounded_activation:
          net = tf.clip_by_value(net, -CLIP_BY_VALUE_CAP, CLIP_BY_VALUE_CAP)
    elif 'pool' in operation:
      net = _pooling(net, stride, operation, self._use_bounded_activation)
      if input_filters != filter_size:
        net = slim.conv2d(net, filter_size, 1, stride=1, scope='1x1')
        net = slim.batch_norm(net, scope='bn_1')
      if self._use_bounded_activation:
        net = tf.clip_by_value(net, -CLIP_BY_VALUE_CAP, CLIP_BY_VALUE_CAP)
    else:
      raise ValueError('Unimplemented operation', operation)

    if operation != 'none':
      net = self._apply_drop_path(net, current_step=current_step)
    return net