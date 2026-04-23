def inception_v4_base(inputs, final_endpoint='Mixed_7d', scope=None):
  """Creates the Inception V4 network up to the given final endpoint.

  Args:
    inputs: a 4-D tensor of size [batch_size, height, width, 3].
    final_endpoint: specifies the endpoint to construct the network up to.
      It can be one of [ 'Conv2d_1a_3x3', 'Conv2d_2a_3x3', 'Conv2d_2b_3x3',
      'Mixed_3a', 'Mixed_4a', 'Mixed_5a', 'Mixed_5b', 'Mixed_5c', 'Mixed_5d',
      'Mixed_5e', 'Mixed_6a', 'Mixed_6b', 'Mixed_6c', 'Mixed_6d', 'Mixed_6e',
      'Mixed_6f', 'Mixed_6g', 'Mixed_6h', 'Mixed_7a', 'Mixed_7b', 'Mixed_7c',
      'Mixed_7d']
    scope: Optional variable_scope.

  Returns:
    logits: the logits outputs of the model.
    end_points: the set of end_points from the inception model.

  Raises:
    ValueError: if final_endpoint is not set to one of the predefined values,
  """
  end_points = {}

  def add_and_check_final(name, net):
    end_points[name] = net
    return name == final_endpoint

  with tf.variable_scope(scope, 'InceptionV4', [inputs]):
    with slim.arg_scope([slim.conv2d, slim.max_pool2d, slim.avg_pool2d],
                        stride=1, padding='SAME'):
      # 299 x 299 x 3
      net = slim.conv2d(inputs, 32, [3, 3], stride=2,
                        padding='VALID', scope='Conv2d_1a_3x3')
      if add_and_check_final('Conv2d_1a_3x3', net): return net, end_points
      # 149 x 149 x 32
      net = slim.conv2d(net, 32, [3, 3], padding='VALID',
                        scope='Conv2d_2a_3x3')
      if add_and_check_final('Conv2d_2a_3x3', net): return net, end_points
      # 147 x 147 x 32
      net = slim.conv2d(net, 64, [3, 3], scope='Conv2d_2b_3x3')
      if add_and_check_final('Conv2d_2b_3x3', net): return net, end_points
      # 147 x 147 x 64
      with tf.variable_scope('Mixed_3a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.max_pool2d(net, [3, 3], stride=2, padding='VALID',
                                     scope='MaxPool_0a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.conv2d(net, 96, [3, 3], stride=2, padding='VALID',
                                 scope='Conv2d_0a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_3a', net): return net, end_points

      # 73 x 73 x 160
      with tf.variable_scope('Mixed_4a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.conv2d(net, 64, [1, 1], scope='Conv2d_0a_1x1')
          branch_0 = slim.conv2d(branch_0, 96, [3, 3], padding='VALID',
                                 scope='Conv2d_1a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.conv2d(net, 64, [1, 1], scope='Conv2d_0a_1x1')
          branch_1 = slim.conv2d(branch_1, 64, [1, 7], scope='Conv2d_0b_1x7')
          branch_1 = slim.conv2d(branch_1, 64, [7, 1], scope='Conv2d_0c_7x1')
          branch_1 = slim.conv2d(branch_1, 96, [3, 3], padding='VALID',
                                 scope='Conv2d_1a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_4a', net): return net, end_points

      # 71 x 71 x 192
      with tf.variable_scope('Mixed_5a'):
        with tf.variable_scope('Branch_0'):
          branch_0 = slim.conv2d(net, 192, [3, 3], stride=2, padding='VALID',
                                 scope='Conv2d_1a_3x3')
        with tf.variable_scope('Branch_1'):
          branch_1 = slim.max_pool2d(net, [3, 3], stride=2, padding='VALID',
                                     scope='MaxPool_1a_3x3')
        net = tf.concat(axis=3, values=[branch_0, branch_1])
        if add_and_check_final('Mixed_5a', net): return net, end_points

      # 35 x 35 x 384
      # 4 x Inception-A blocks
      for idx in range(4):
        block_scope = 'Mixed_5' + chr(ord('b') + idx)
        net = block_inception_a(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points

      # 35 x 35 x 384
      # Reduction-A block
      net = block_reduction_a(net, 'Mixed_6a')
      if add_and_check_final('Mixed_6a', net): return net, end_points

      # 17 x 17 x 1024
      # 7 x Inception-B blocks
      for idx in range(7):
        block_scope = 'Mixed_6' + chr(ord('b') + idx)
        net = block_inception_b(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points

      # 17 x 17 x 1024
      # Reduction-B block
      net = block_reduction_b(net, 'Mixed_7a')
      if add_and_check_final('Mixed_7a', net): return net, end_points

      # 8 x 8 x 1536
      # 3 x Inception-C blocks
      for idx in range(3):
        block_scope = 'Mixed_7' + chr(ord('b') + idx)
        net = block_inception_c(net, block_scope)
        if add_and_check_final(block_scope, net): return net, end_points
  raise ValueError('Unknown final endpoint %s' % final_endpoint)