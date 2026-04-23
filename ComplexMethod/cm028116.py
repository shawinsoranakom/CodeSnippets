def inception_v3(inputs,
                 num_classes=1000,
                 is_training=True,
                 dropout_keep_prob=0.8,
                 min_depth=16,
                 depth_multiplier=1.0,
                 prediction_fn=slim.softmax,
                 spatial_squeeze=True,
                 reuse=None,
                 create_aux_logits=True,
                 scope='InceptionV3',
                 global_pool=False):
  """Inception model from http://arxiv.org/abs/1512.00567.

  "Rethinking the Inception Architecture for Computer Vision"

  Christian Szegedy, Vincent Vanhoucke, Sergey Ioffe, Jonathon Shlens,
  Zbigniew Wojna.

  With the default arguments this method constructs the exact model defined in
  the paper. However, one can experiment with variations of the inception_v3
  network by changing arguments dropout_keep_prob, min_depth and
  depth_multiplier.

  The default image size used to train this network is 299x299.

  Args:
    inputs: a tensor of size [batch_size, height, width, channels].
    num_classes: number of predicted classes. If 0 or None, the logits layer
      is omitted and the input features to the logits layer (before dropout)
      are returned instead.
    is_training: whether is training or not.
    dropout_keep_prob: the percentage of activation values that are retained.
    min_depth: Minimum depth value (number of channels) for all convolution ops.
      Enforced when depth_multiplier < 1, and not an active constraint when
      depth_multiplier >= 1.
    depth_multiplier: Float multiplier for the depth (number of channels)
      for all convolution ops. The value must be greater than zero. Typical
      usage will be to set this value in (0, 1) to reduce the number of
      parameters or computation cost of the model.
    prediction_fn: a function to get predictions out of logits.
    spatial_squeeze: if True, logits is of shape [B, C], if false logits is of
        shape [B, 1, 1, C], where B is batch_size and C is number of classes.
    reuse: whether or not the network and its variables should be reused. To be
      able to reuse 'scope' must be given.
    create_aux_logits: Whether to create the auxiliary logits.
    scope: Optional variable_scope.
    global_pool: Optional boolean flag to control the avgpooling before the
      logits layer. If false or unset, pooling is done with a fixed window
      that reduces default-sized inputs to 1x1, while larger inputs lead to
      larger outputs. If true, any input size is pooled down to 1x1.

  Returns:
    net: a Tensor with the logits (pre-softmax activations) if num_classes
      is a non-zero integer, or the non-dropped-out input to the logits layer
      if num_classes is 0 or None.
    end_points: a dictionary from components of the network to the corresponding
      activation.

  Raises:
    ValueError: if 'depth_multiplier' is less than or equal to zero.
  """
  if depth_multiplier <= 0:
    raise ValueError('depth_multiplier is not greater than zero.')
  depth = lambda d: max(int(d * depth_multiplier), min_depth)

  with tf.variable_scope(
      scope, 'InceptionV3', [inputs], reuse=reuse) as scope:
    with slim.arg_scope([slim.batch_norm, slim.dropout],
                        is_training=is_training):
      net, end_points = inception_v3_base(
          inputs, scope=scope, min_depth=min_depth,
          depth_multiplier=depth_multiplier)

      # Auxiliary Head logits
      if create_aux_logits and num_classes:
        with slim.arg_scope([slim.conv2d, slim.max_pool2d, slim.avg_pool2d],
                            stride=1, padding='SAME'):
          aux_logits = end_points['Mixed_6e']
          with tf.variable_scope('AuxLogits'):
            aux_logits = slim.avg_pool2d(
                aux_logits, [5, 5], stride=3, padding='VALID',
                scope='AvgPool_1a_5x5')
            aux_logits = slim.conv2d(aux_logits, depth(128), [1, 1],
                                     scope='Conv2d_1b_1x1')

            # Shape of feature map before the final layer.
            kernel_size = _reduced_kernel_size_for_small_input(
                aux_logits, [5, 5])
            aux_logits = slim.conv2d(
                aux_logits, depth(768), kernel_size,
                weights_initializer=trunc_normal(0.01),
                padding='VALID', scope='Conv2d_2a_{}x{}'.format(*kernel_size))
            aux_logits = slim.conv2d(
                aux_logits, num_classes, [1, 1], activation_fn=None,
                normalizer_fn=None, weights_initializer=trunc_normal(0.001),
                scope='Conv2d_2b_1x1')
            if spatial_squeeze:
              aux_logits = tf.squeeze(aux_logits, [1, 2], name='SpatialSqueeze')
            end_points['AuxLogits'] = aux_logits

      # Final pooling and prediction
      with tf.variable_scope('Logits'):
        if global_pool:
          # Global average pooling.
          net = tf.reduce_mean(
              input_tensor=net, axis=[1, 2], keepdims=True, name='GlobalPool')
          end_points['global_pool'] = net
        else:
          # Pooling with a fixed kernel size.
          kernel_size = _reduced_kernel_size_for_small_input(net, [8, 8])
          net = slim.avg_pool2d(net, kernel_size, padding='VALID',
                                scope='AvgPool_1a_{}x{}'.format(*kernel_size))
          end_points['AvgPool_1a'] = net
        if not num_classes:
          return net, end_points
        # 1 x 1 x 2048
        net = slim.dropout(net, keep_prob=dropout_keep_prob, scope='Dropout_1b')
        end_points['PreLogits'] = net
        # 2048
        logits = slim.conv2d(net, num_classes, [1, 1], activation_fn=None,
                             normalizer_fn=None, scope='Conv2d_1c_1x1')
        if spatial_squeeze:
          logits = tf.squeeze(logits, [1, 2], name='SpatialSqueeze')
        # 1000
      end_points['Logits'] = logits
      end_points['Predictions'] = prediction_fn(logits, scope='Predictions')
  return logits, end_points