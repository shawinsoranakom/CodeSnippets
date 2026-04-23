def s3dg_base(inputs,
              first_temporal_kernel_size=3,
              temporal_conv_startat='Conv2d_2c_3x3',
              gating_startat='Conv2d_2c_3x3',
              final_endpoint='Mixed_5c',
              min_depth=16,
              depth_multiplier=1.0,
              data_format='NDHWC',
              scope='InceptionV1'):
  """Defines the I3D/S3DG base architecture.

  Note that we use the names as defined in Inception V1 to facilitate checkpoint
  conversion from an image-trained Inception V1 checkpoint to I3D checkpoint.

  Args:
    inputs: A 5-D float tensor of size [batch_size, num_frames, height, width,
      channels].
    first_temporal_kernel_size: Specifies the temporal kernel size for the first
      conv3d filter. A larger value slows down the model but provides little
      accuracy improvement. The default is 7 in the original I3D and S3D-G but 3
      gives better performance. Must be set to one of 1, 3, 5 or 7.
    temporal_conv_startat: Specifies the first conv block to use 3D or separable
      3D convs rather than 2D convs (implemented as [1, k, k] 3D conv). This is
      used to construct the inverted pyramid models. 'Conv2d_2c_3x3' is the
      first valid block to use separable 3D convs. If provided block name is
      not present, all valid blocks will use separable 3D convs. Note that
      'Conv2d_1a_7x7' cannot be made into a separable 3D conv, but can be made
      into a 2D or 3D conv using the `first_temporal_kernel_size` option.
    gating_startat: Specifies the first conv block to use self gating.
      'Conv2d_2c_3x3' is the first valid block to use self gating. If provided
      block name is not present, all valid blocks will use separable 3D convs.
    final_endpoint: Specifies the endpoint to construct the network up to. It
      can be one of ['Conv2d_1a_7x7', 'MaxPool_2a_3x3', 'Conv2d_2b_1x1',
      'Conv2d_2c_3x3', 'MaxPool_3a_3x3', 'Mixed_3b', 'Mixed_3c',
      'MaxPool_4a_3x3', 'Mixed_4b', 'Mixed_4c', 'Mixed_4d', 'Mixed_4e',
      'Mixed_4f', 'MaxPool_5a_2x2', 'Mixed_5b', 'Mixed_5c']
    min_depth: Minimum depth value (number of channels) for all convolution ops.
      Enforced when depth_multiplier < 1, and not an active constraint when
      depth_multiplier >= 1.
    depth_multiplier: Float multiplier for the depth (number of channels)
      for all convolution ops. The value must be greater than zero. Typical
      usage will be to set this value in (0, 1) to reduce the number of
      parameters or computation cost of the model.
    data_format: An optional string from: "NDHWC", "NCDHW". Defaults to "NDHWC".
      The data format of the input and output data. With the default format
      "NDHWC", the data is stored in the order of: [batch, in_depth, in_height,
      in_width, in_channels]. Alternatively, the format could be "NCDHW", the
      data storage order is:
      [batch, in_channels, in_depth, in_height, in_width].
    scope: Optional variable_scope.

  Returns:
    A dictionary from components of the network to the corresponding activation.

  Raises:
    ValueError: if final_endpoint is not set to one of the predefined values, or
      if depth_multiplier <= 0.
  """

  assert data_format in ['NDHWC', 'NCDHW']
  end_points = {}
  t = 1
  # For inverted pyramid models, we start with gating switched off.
  use_gating = False
  self_gating_fn = None
  def gating_fn(inputs, scope):
    return self_gating(inputs, scope, data_format=data_format)

  if depth_multiplier <= 0:
    raise ValueError('depth_multiplier is not greater than zero.')
  depth = lambda d: max(int(d * depth_multiplier), min_depth)

  with tf.variable_scope(scope, 'InceptionV1', [inputs]):
    with arg_scope([slim.conv3d], weights_initializer=trunc_normal(0.01)):
      with arg_scope([slim.conv3d, slim.max_pool3d, conv3d_spatiotemporal],
                     stride=1,
                     data_format=data_format,
                     padding='SAME'):
        # batch_size x 32 x 112 x 112 x 64
        end_point = 'Conv2d_1a_7x7'
        if first_temporal_kernel_size not in [1, 3, 5, 7]:
          raise ValueError(
              'first_temporal_kernel_size can only be 1, 3, 5 or 7.')
        # Separable conv is slow when used at first conv layer.
        net = conv3d_spatiotemporal(
            inputs,
            depth(64), [first_temporal_kernel_size, 7, 7],
            stride=2,
            separable=False,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points
        # batch_size x 32 x 56 x 56 x 64
        end_point = 'MaxPool_2a_3x3'
        net = slim.max_pool3d(net, [1, 3, 3], stride=[1, 2, 2], scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points
        # batch_size x 32 x 56 x 56 x 64
        end_point = 'Conv2d_2b_1x1'
        net = slim.conv3d(net, depth(64), [1, 1, 1], scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points
        # batch_size x 32 x 56 x 56 x 192
        end_point = 'Conv2d_2c_3x3'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = conv3d_spatiotemporal(net, depth(192), [t, 3, 3], scope=end_point)
        if use_gating:
          net = self_gating(net, scope=end_point, data_format=data_format)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points
        # batch_size x 32 x 28 x 28 x 192
        end_point = 'MaxPool_3a_3x3'
        net = slim.max_pool3d(net, [1, 3, 3], stride=[1, 2, 2], scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 32 x 28 x 28 x 256
        end_point = 'Mixed_3b'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(64),
            num_outputs_1_0a=depth(96),
            num_outputs_1_0b=depth(128),
            num_outputs_2_0a=depth(16),
            num_outputs_2_0b=depth(32),
            num_outputs_3_0b=depth(32),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        end_point = 'Mixed_3c'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(128),
            num_outputs_1_0a=depth(128),
            num_outputs_1_0b=depth(192),
            num_outputs_2_0a=depth(32),
            num_outputs_2_0b=depth(96),
            num_outputs_3_0b=depth(64),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        end_point = 'MaxPool_4a_3x3'
        net = slim.max_pool3d(net, [3, 3, 3], stride=[2, 2, 2], scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 16 x 14 x 14 x 512
        end_point = 'Mixed_4b'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(192),
            num_outputs_1_0a=depth(96),
            num_outputs_1_0b=depth(208),
            num_outputs_2_0a=depth(16),
            num_outputs_2_0b=depth(48),
            num_outputs_3_0b=depth(64),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 16 x 14 x 14 x 512
        end_point = 'Mixed_4c'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(160),
            num_outputs_1_0a=depth(112),
            num_outputs_1_0b=depth(224),
            num_outputs_2_0a=depth(24),
            num_outputs_2_0b=depth(64),
            num_outputs_3_0b=depth(64),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 16 x 14 x 14 x 512
        end_point = 'Mixed_4d'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(128),
            num_outputs_1_0a=depth(128),
            num_outputs_1_0b=depth(256),
            num_outputs_2_0a=depth(24),
            num_outputs_2_0b=depth(64),
            num_outputs_3_0b=depth(64),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 16 x 14 x 14 x 528
        end_point = 'Mixed_4e'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(112),
            num_outputs_1_0a=depth(144),
            num_outputs_1_0b=depth(288),
            num_outputs_2_0a=depth(32),
            num_outputs_2_0b=depth(64),
            num_outputs_3_0b=depth(64),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 16 x 14 x 14 x 832
        end_point = 'Mixed_4f'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(256),
            num_outputs_1_0a=depth(160),
            num_outputs_1_0b=depth(320),
            num_outputs_2_0a=depth(32),
            num_outputs_2_0b=depth(128),
            num_outputs_3_0b=depth(128),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        end_point = 'MaxPool_5a_2x2'
        net = slim.max_pool3d(net, [2, 2, 2], stride=[2, 2, 2], scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 8 x 7 x 7 x 832
        end_point = 'Mixed_5b'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(256),
            num_outputs_1_0a=depth(160),
            num_outputs_1_0b=depth(320),
            num_outputs_2_0a=depth(32),
            num_outputs_2_0b=depth(128),
            num_outputs_3_0b=depth(128),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points

        # batch_size x 8 x 7 x 7 x 1024
        end_point = 'Mixed_5c'
        if temporal_conv_startat == end_point:
          t = 3
        if gating_startat == end_point:
          use_gating = True
          self_gating_fn = gating_fn
        net = inception_block_v1_3d(
            net,
            num_outputs_0_0a=depth(384),
            num_outputs_1_0a=depth(192),
            num_outputs_1_0b=depth(384),
            num_outputs_2_0a=depth(48),
            num_outputs_2_0b=depth(128),
            num_outputs_3_0b=depth(128),
            temporal_kernel_size=t,
            self_gating_fn=self_gating_fn,
            data_format=data_format,
            scope=end_point)
        end_points[end_point] = net
        if final_endpoint == end_point:
          return net, end_points
    raise ValueError('Unknown final endpoint %s' % final_endpoint)