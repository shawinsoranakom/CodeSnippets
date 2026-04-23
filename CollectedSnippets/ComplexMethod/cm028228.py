def __init__(self,
               num_levels,
               depth,
               is_training,
               conv_hyperparams,
               freeze_batchnorm,
               use_depthwise=False,
               use_explicit_padding=False,
               use_bounded_activations=False,
               use_native_resize_op=False,
               scope=None,
               name=None):
    """Constructor.

    Args:
      num_levels: the number of image features.
      depth: depth of output feature maps.
      is_training: Indicates whether the feature generator is in training mode.
      conv_hyperparams: A `hyperparams_builder.KerasLayerHyperparams` object
        containing hyperparameters for convolution ops.
      freeze_batchnorm: Bool. Whether to freeze batch norm parameters during
        training or not. When training with a small batch size (e.g. 1), it is
        desirable to freeze batch norm update and use pretrained batch norm
        params.
      use_depthwise: whether to use depthwise separable conv instead of regular
        conv.
      use_explicit_padding: whether to use explicit padding.
      use_bounded_activations: Whether or not to clip activations to range
        [-ACTIVATION_BOUND, ACTIVATION_BOUND]. Bounded activations better lend
        themselves to quantized inference.
      use_native_resize_op: If True, uses tf.image.resize_nearest_neighbor op
        for the upsampling process instead of reshape and broadcasting
        implementation.
      scope: A scope name to wrap this op under.
      name: A string name scope to assign to the model. If 'None', Keras
        will auto-generate one from the class name.
    """
    super(KerasFpnTopDownFeatureMaps, self).__init__(name=name)

    self.scope = scope if scope else 'top_down'
    self.top_layers = []
    self.residual_blocks = []
    self.top_down_blocks = []
    self.reshape_blocks = []
    self.conv_layers = []

    padding = 'VALID' if use_explicit_padding else 'SAME'
    stride = 1
    kernel_size = 3
    def clip_by_value(features):
      return tf.clip_by_value(features, -ACTIVATION_BOUND, ACTIVATION_BOUND)

    # top layers
    self.top_layers.append(tf.keras.layers.Conv2D(
        depth, [1, 1], strides=stride, padding=padding,
        name='projection_%d' % num_levels,
        **conv_hyperparams.params(use_bias=True)))
    if use_bounded_activations:
      self.top_layers.append(tf.keras.layers.Lambda(
          clip_by_value, name='clip_by_value'))

    for level in reversed(list(range(num_levels - 1))):
      # to generate residual from image features
      residual_net = []
      # to preprocess top_down (the image feature map from last layer)
      top_down_net = []
      # to reshape top_down according to residual if necessary
      reshaped_residual = []
      # to apply convolution layers to feature map
      conv_net = []

      # residual block
      residual_net.append(tf.keras.layers.Conv2D(
          depth, [1, 1], padding=padding, strides=1,
          name='projection_%d' % (level + 1),
          **conv_hyperparams.params(use_bias=True)))
      if use_bounded_activations:
        residual_net.append(tf.keras.layers.Lambda(
            clip_by_value, name='clip_by_value'))

      # top-down block
      # TODO (b/128922690): clean-up of ops.nearest_neighbor_upsampling
      if use_native_resize_op:
        def resize_nearest_neighbor(image):
          image_shape = shape_utils.combined_static_and_dynamic_shape(image)
          return tf.image.resize_nearest_neighbor(
              image, [image_shape[1] * 2, image_shape[2] * 2])
        top_down_net.append(tf.keras.layers.Lambda(
            resize_nearest_neighbor, name='nearest_neighbor_upsampling'))
      else:
        def nearest_neighbor_upsampling(image):
          return ops.nearest_neighbor_upsampling(image, scale=2)
        top_down_net.append(tf.keras.layers.Lambda(
            nearest_neighbor_upsampling, name='nearest_neighbor_upsampling'))

      # reshape block
      if use_explicit_padding:
        def reshape(inputs):
          residual_shape = tf.shape(inputs[0])
          return inputs[1][:, :residual_shape[1], :residual_shape[2], :]
        reshaped_residual.append(
            tf.keras.layers.Lambda(reshape, name='reshape'))

      # down layers
      if use_bounded_activations:
        conv_net.append(tf.keras.layers.Lambda(
            clip_by_value, name='clip_by_value'))

      if use_explicit_padding:
        def fixed_padding(features, kernel_size=kernel_size):
          return ops.fixed_padding(features, kernel_size)
        conv_net.append(tf.keras.layers.Lambda(
            fixed_padding, name='fixed_padding'))

      layer_name = 'smoothing_%d' % (level + 1)
      conv_block = create_conv_block(
          use_depthwise, kernel_size, padding, stride, layer_name,
          conv_hyperparams, is_training, freeze_batchnorm, depth)
      conv_net.extend(conv_block)

      self.residual_blocks.append(residual_net)
      self.top_down_blocks.append(top_down_net)
      self.reshape_blocks.append(reshaped_residual)
      self.conv_layers.append(conv_net)