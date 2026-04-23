def inception_v1_stem_cells(
    inputs: tf.Tensor,
    depth_multiplier: float,
    final_endpoint: Text,
    temporal_conv_endpoints: Optional[Set[Text]] = None,
    self_gating_endpoints: Optional[Set[Text]] = None,
    temporal_conv_type: Text = '3d',
    first_temporal_kernel_size: int = 7,
    use_sync_bn: bool = False,
    norm_momentum: float = 0.999,
    norm_epsilon: float = 0.001,
    temporal_conv_initializer: Union[
        Text, initializers.Initializer] = initializers.TruncatedNormal(
            mean=0.0, stddev=0.01),
    kernel_initializer: Union[Text,
                              initializers.Initializer] = 'truncated_normal',
    kernel_regularizer: Union[Text, regularizers.Regularizer] = 'l2',
    parameterized_conv_layer: Type[
        net_utils.ParameterizedConvLayer] = net_utils.ParameterizedConvLayer,
    layer_naming_fn: Callable[[Text], Text] = lambda end_point: None,
) -> Tuple[tf.Tensor, Dict[Text, tf.Tensor]]:
  """Stem cells used in the original I3D/S3D model.

  Args:
    inputs: A 5-D float tensor of size [batch_size, num_frames, height, width,
      channels].
    depth_multiplier: A float to reduce/increase number of channels.
    final_endpoint: Specifies the endpoint to construct the network up to. It
      can be one of ['Conv2d_1a_7x7', 'MaxPool_2a_3x3', 'Conv2d_2b_1x1',
      'Conv2d_2c_3x3', 'MaxPool_3a_3x3'].
    temporal_conv_endpoints: Specifies the endpoints where to perform temporal
      convolution.
    self_gating_endpoints: Specifies the endpoints where to perform self gating.
    temporal_conv_type: '3d' for I3D model and '2+1d' for S3D model.
    first_temporal_kernel_size: temporal kernel size of the first convolution
      layer.
    use_sync_bn: If True, use synchronized batch normalization.
    norm_momentum: A `float` of normalization momentum for the moving average.
    norm_epsilon: A `float` added to variance to avoid dividing by zero.
    temporal_conv_initializer: Weight initializer for temporal convolution
      inside the cell. It only applies to 2+1d and 1+2d cases.
    kernel_initializer: Weight initializer for convolutional layers other than
      temporal convolution.
    kernel_regularizer: Weight regularizer for all convolutional layers.
    parameterized_conv_layer: class for parameterized conv layer.
    layer_naming_fn: function to customize conv / pooling layer names given
      endpoint name of the block. This is mainly used to creat model that is
      compatible with TF1 checkpoints.

  Returns:
    A dictionary from components of the network to the corresponding activation.
  """

  if temporal_conv_endpoints is None:
    temporal_conv_endpoints = set()
  if self_gating_endpoints is None:
    self_gating_endpoints = set()
  if use_sync_bn:
    batch_norm = tf_keras.layers.experimental.SyncBatchNormalization
  else:
    batch_norm = tf_keras.layers.BatchNormalization
  if tf_keras.backend.image_data_format() == 'channels_last':
    bn_axis = -1
  else:
    bn_axis = 1

  end_points = {}
  # batch_size x 32 x 112 x 112 x 64
  end_point = 'Conv2d_1a_7x7'
  net = tf_keras.layers.Conv3D(
      filters=net_utils.apply_depth_multiplier(64, depth_multiplier),
      kernel_size=[first_temporal_kernel_size, 7, 7],
      strides=[2, 2, 2],
      padding='same',
      use_bias=False,
      kernel_initializer=tf_utils.clone_initializer(kernel_initializer),
      kernel_regularizer=kernel_regularizer,
      name=layer_naming_fn(end_point))(
          inputs)
  net = batch_norm(
      axis=bn_axis,
      momentum=norm_momentum,
      epsilon=norm_epsilon,
      scale=False,
      gamma_initializer='ones',
      name=layer_naming_fn(end_point + '/BatchNorm'))(
          net)
  net = tf.nn.relu(net)
  end_points[end_point] = net
  if final_endpoint == end_point:
    return net, end_points
  # batch_size x 32 x 56 x 56 x 64
  end_point = 'MaxPool_2a_3x3'
  net = tf_keras.layers.MaxPool3D(
      pool_size=[1, 3, 3],
      strides=[1, 2, 2],
      padding='same',
      name=layer_naming_fn(end_point))(
          net)
  end_points[end_point] = net
  if final_endpoint == end_point:
    return net, end_points
  # batch_size x 32 x 56 x 56 x 64
  end_point = 'Conv2d_2b_1x1'
  net = tf_keras.layers.Conv3D(
      filters=net_utils.apply_depth_multiplier(64, depth_multiplier),
      strides=[1, 1, 1],
      kernel_size=[1, 1, 1],
      padding='same',
      use_bias=False,
      kernel_initializer=tf_utils.clone_initializer(kernel_initializer),
      kernel_regularizer=kernel_regularizer,
      name=layer_naming_fn(end_point))(
          net)
  net = batch_norm(
      axis=bn_axis,
      momentum=norm_momentum,
      epsilon=norm_epsilon,
      scale=False,
      gamma_initializer='ones',
      name=layer_naming_fn(end_point + '/BatchNorm'))(
          net)
  net = tf.nn.relu(net)
  end_points[end_point] = net
  if final_endpoint == end_point:
    return net, end_points
  # batch_size x 32 x 56 x 56 x 192
  end_point = 'Conv2d_2c_3x3'
  if end_point not in temporal_conv_endpoints:
    temporal_conv_type = '2d'
  net = parameterized_conv_layer(
      conv_type=temporal_conv_type,
      kernel_size=3,
      filters=net_utils.apply_depth_multiplier(192, depth_multiplier),
      strides=[1, 1, 1],
      rates=[1, 1, 1],
      use_sync_bn=use_sync_bn,
      norm_momentum=norm_momentum,
      norm_epsilon=norm_epsilon,
      temporal_conv_initializer=temporal_conv_initializer,
      kernel_initializer=tf_utils.clone_initializer(kernel_initializer),
      kernel_regularizer=kernel_regularizer,
      name=layer_naming_fn(end_point))(
          net)
  if end_point in self_gating_endpoints:
    net = nn_blocks_3d.SelfGating(
        filters=net_utils.apply_depth_multiplier(192, depth_multiplier),
        name=layer_naming_fn(end_point + '/self_gating'))(
            net)
  end_points[end_point] = net
  if final_endpoint == end_point:
    return net, end_points
  # batch_size x 32 x 28 x 28 x 192
  end_point = 'MaxPool_3a_3x3'
  net = tf_keras.layers.MaxPool3D(
      pool_size=[1, 3, 3],
      strides=[1, 2, 2],
      padding='same',
      name=layer_naming_fn(end_point))(
          net)
  end_points[end_point] = net
  return net, end_points