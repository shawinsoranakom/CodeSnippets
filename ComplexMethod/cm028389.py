def _build_nas_base(images,
                    cell,
                    backbone,
                    num_classes,
                    hparams,
                    global_pool=False,
                    output_stride=16,
                    nas_use_classification_head=False,
                    reuse=None,
                    scope=None,
                    final_endpoint=None,
                    batch_norm_fn=slim.batch_norm,
                    nas_remove_os32_stride=False):
  """Constructs a NAS model.

  Args:
    images: A tensor of size [batch, height, width, channels].
    cell: Cell structure used in the network.
    backbone: Backbone structure used in the network. A list of integers in
      which value 0 means "output_stride=4", value 1 means "output_stride=8",
      value 2 means "output_stride=16", and value 3 means "output_stride=32".
    num_classes: Number of classes to predict.
    hparams: Hyperparameters needed to construct the network.
    global_pool: If True, we perform global average pooling before computing the
      logits. Set to True for image classification, False for dense prediction.
    output_stride: Interger, the stride of output feature maps.
    nas_use_classification_head: Boolean, use image classification head.
    reuse: Whether or not the network and its variables should be reused. To be
      able to reuse 'scope' must be given.
    scope: Optional variable_scope.
    final_endpoint: The endpoint to construct the network up to.
    batch_norm_fn: Batch norm function.
    nas_remove_os32_stride: Boolean, remove stride in output_stride 32 branch.

  Returns:
    net: A rank-4 tensor of size [batch, height_out, width_out, channels_out].
    end_points: A dictionary from components of the network to the corresponding
      activation.

  Raises:
    ValueError: If output_stride is not a multiple of backbone output stride.
  """
  with tf.variable_scope(scope, 'nas', [images], reuse=reuse):
    end_points = {}
    def add_and_check_endpoint(endpoint_name, net):
      end_points[endpoint_name] = net
      return final_endpoint and (endpoint_name == final_endpoint)

    net, cell_outputs = _nas_stem(images,
                                  batch_norm_fn=batch_norm_fn)
    if add_and_check_endpoint('Stem', net):
      return net, end_points

    # Run the cells
    filter_scaling = 1.0
    for cell_num in range(len(backbone)):
      stride = 1
      if cell_num == 0:
        if backbone[0] == 1:
          stride = 2
          filter_scaling *= hparams.filter_scaling_rate
      else:
        if backbone[cell_num] == backbone[cell_num - 1] + 1:
          stride = 2
          if backbone[cell_num] == 3 and nas_remove_os32_stride:
            stride = 1
          filter_scaling *= hparams.filter_scaling_rate
        elif backbone[cell_num] == backbone[cell_num - 1] - 1:
          if backbone[cell_num - 1] == 3 and nas_remove_os32_stride:
            # No need to rescale features.
            pass
          else:
            # Scale features by a factor of 2.
            scaled_height = scale_dimension(net.shape[1].value, 2)
            scaled_width = scale_dimension(net.shape[2].value, 2)
            net = resize_bilinear(net, [scaled_height, scaled_width], net.dtype)
          filter_scaling /= hparams.filter_scaling_rate
      net = cell(
          net,
          scope='cell_{}'.format(cell_num),
          filter_scaling=filter_scaling,
          stride=stride,
          prev_layer=cell_outputs[-2],
          cell_num=cell_num)
      if add_and_check_endpoint('Cell_{}'.format(cell_num), net):
        return net, end_points
      cell_outputs.append(net)
    net = tf.nn.relu(net)

    if nas_use_classification_head:
      # Add image classification head.
      # We will expand the filters for different output_strides.
      output_stride_to_expanded_filters = {8: 256, 16: 512, 32: 1024}
      current_output_scale = 2 + backbone[-1]
      current_output_stride = 2 ** current_output_scale
      if output_stride % current_output_stride != 0:
        raise ValueError(
            'output_stride must be a multiple of backbone output stride.')
      output_stride //= current_output_stride
      rate = 1
      if current_output_stride != 32:
        num_downsampling = 5 - current_output_scale
        for i in range(num_downsampling):
          # Gradually donwsample feature maps to output stride = 32.
          target_output_stride = 2 ** (current_output_scale + 1 + i)
          target_filters = output_stride_to_expanded_filters[
              target_output_stride]
          scope = 'downsample_os{}'.format(target_output_stride)
          if output_stride != 1:
            stride = 2
            output_stride //= 2
          else:
            stride = 1
            rate *= 2
          net = resnet_utils.conv2d_same(
              net, target_filters, 3, stride=stride, rate=rate,
              scope=scope + '_conv')
          net = batch_norm_fn(net, scope=scope + '_bn')
          add_and_check_endpoint(scope, net)
          net = tf.nn.relu(net)
      # Apply 1x1 convolution to expand dimension to 2048.
      scope = 'classification_head'
      net = slim.conv2d(net, 2048, 1, scope=scope + '_conv')
      net = batch_norm_fn(net, scope=scope + '_bn')
      add_and_check_endpoint(scope, net)
      net = tf.nn.relu(net)
    if global_pool:
      # Global average pooling.
      net = tf.reduce_mean(net, [1, 2], name='global_pool', keepdims=True)
    if num_classes is not None:
      net = slim.conv2d(net, num_classes, 1, activation_fn=None,
                        normalizer_fn=None, scope='logits')
      end_points['predictions'] = slim.softmax(net, scope='predictions')
    return net, end_points