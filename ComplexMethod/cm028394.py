def _apply_conv_operation(self, net, operation, stride,
                            is_from_original_input):
    """Applies the predicted conv operation to net."""
    if stride > 1 and not is_from_original_input:
      stride = 1
    input_filters = net.shape[3]
    filter_size = self._filter_size
    if 'separable' in operation:
      num_layers = int(operation.split('_')[-1])
      kernel_size = int(operation.split('x')[0][-1])
      for layer_num in range(num_layers):
        net = tf.nn.relu(net)
        net = separable_conv2d_same(
            net,
            filter_size,
            kernel_size,
            depth_multiplier=1,
            scope='separable_{0}x{0}_{1}'.format(kernel_size, layer_num + 1),
            stride=stride)
        net = self._batch_norm_fn(
            net, scope='bn_sep_{0}x{0}_{1}'.format(kernel_size, layer_num + 1))
        stride = 1
    elif 'atrous' in operation:
      kernel_size = int(operation.split('x')[0][-1])
      net = tf.nn.relu(net)
      if stride == 2:
        scaled_height = scale_dimension(tf.shape(net)[1], 0.5)
        scaled_width = scale_dimension(tf.shape(net)[2], 0.5)
        net = resize_bilinear(net, [scaled_height, scaled_width], net.dtype)
        net = resnet_utils.conv2d_same(
            net, filter_size, kernel_size, rate=1, stride=1,
            scope='atrous_{0}x{0}'.format(kernel_size))
      else:
        net = resnet_utils.conv2d_same(
            net, filter_size, kernel_size, rate=2, stride=1,
            scope='atrous_{0}x{0}'.format(kernel_size))
      net = self._batch_norm_fn(net, scope='bn_atr_{0}x{0}'.format(kernel_size))
    elif operation in ['none']:
      if stride > 1 or (input_filters != filter_size):
        net = tf.nn.relu(net)
        net = slim.conv2d(net, filter_size, 1, stride=stride, scope='1x1')
        net = self._batch_norm_fn(net, scope='bn_1')
    elif 'pool' in operation:
      pooling_type = operation.split('_')[0]
      pooling_shape = int(operation.split('_')[-1].split('x')[0])
      if pooling_type == 'avg':
        net = slim.avg_pool2d(net, pooling_shape, stride=stride, padding='SAME')
      elif pooling_type == 'max':
        net = slim.max_pool2d(net, pooling_shape, stride=stride, padding='SAME')
      else:
        raise ValueError('Unimplemented pooling type: ', pooling_type)
      if input_filters != filter_size:
        net = slim.conv2d(net, filter_size, 1, stride=1, scope='1x1')
        net = self._batch_norm_fn(net, scope='bn_1')
    else:
      raise ValueError('Unimplemented operation', operation)

    if operation != 'none':
      net = self._apply_drop_path(net)
    return net