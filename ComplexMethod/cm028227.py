def __init__(self,
               feature_map_layout,
               depth_multiplier,
               min_depth,
               insert_1x1_conv,
               is_training,
               conv_hyperparams,
               freeze_batchnorm,
               name=None):
    """Constructor.

    Args:
      feature_map_layout: Dictionary of specifications for the feature map
        layouts in the following format (Inception V2/V3 respectively):
        {
          'from_layer': ['Mixed_3c', 'Mixed_4c', 'Mixed_5c', '', '', ''],
          'layer_depth': [-1, -1, -1, 512, 256, 128]
        }
        or
        {
          'from_layer': ['Mixed_5d', 'Mixed_6e', 'Mixed_7c', '', '', ''],
          'layer_depth': [-1, -1, -1, 512, 256, 128]
        }
        If 'from_layer' is specified, the specified feature map is directly used
        as a box predictor layer, and the layer_depth is directly infered from
        the feature map (instead of using the provided 'layer_depth' parameter).
        In this case, our convention is to set 'layer_depth' to -1 for clarity.
        Otherwise, if 'from_layer' is an empty string, then the box predictor
        layer will be built from the previous layer using convolution
        operations. Note that the current implementation only supports
        generating new layers using convolutions of stride 2 (resulting in a
        spatial resolution reduction by a factor of 2), and will be extended to
        a more flexible design. Convolution kernel size is set to 3 by default,
        and can be customized by 'conv_kernel_size' parameter (similarily,
        'conv_kernel_size' should be set to -1 if 'from_layer' is specified).
        The created convolution operation will be a normal 2D convolution by
        default, and a depthwise convolution followed by 1x1 convolution if
        'use_depthwise' is set to True.
      depth_multiplier: Depth multiplier for convolutional layers.
      min_depth: Minimum depth for convolutional layers.
      insert_1x1_conv: A boolean indicating whether an additional 1x1
        convolution should be inserted before shrinking the feature map.
      is_training: Indicates whether the feature generator is in training mode.
      conv_hyperparams: A `hyperparams_builder.KerasLayerHyperparams` object
        containing hyperparameters for convolution ops.
      freeze_batchnorm: Bool. Whether to freeze batch norm parameters during
        training or not. When training with a small batch size (e.g. 1), it is
        desirable to freeze batch norm update and use pretrained batch norm
        params.
      name: A string name scope to assign to the model. If 'None', Keras
        will auto-generate one from the class name.
    """
    super(KerasMultiResolutionFeatureMaps, self).__init__(name=name)

    self.feature_map_layout = feature_map_layout
    self.convolutions = []

    depth_fn = get_depth_fn(depth_multiplier, min_depth)

    base_from_layer = ''
    use_explicit_padding = False
    if 'use_explicit_padding' in feature_map_layout:
      use_explicit_padding = feature_map_layout['use_explicit_padding']
    use_depthwise = False
    if 'use_depthwise' in feature_map_layout:
      use_depthwise = feature_map_layout['use_depthwise']
    for index, from_layer in enumerate(feature_map_layout['from_layer']):
      net = []
      layer_depth = feature_map_layout['layer_depth'][index]
      conv_kernel_size = 3
      if 'conv_kernel_size' in feature_map_layout:
        conv_kernel_size = feature_map_layout['conv_kernel_size'][index]
      if from_layer:
        base_from_layer = from_layer
      else:
        if insert_1x1_conv:
          layer_name = '{}_1_Conv2d_{}_1x1_{}'.format(
              base_from_layer, index, depth_fn(layer_depth // 2))
          net.append(tf.keras.layers.Conv2D(depth_fn(layer_depth // 2),
                                            [1, 1],
                                            padding='SAME',
                                            strides=1,
                                            name=layer_name + '_conv',
                                            **conv_hyperparams.params()))
          net.append(
              conv_hyperparams.build_batch_norm(
                  training=(is_training and not freeze_batchnorm),
                  name=layer_name + '_batchnorm'))
          net.append(
              conv_hyperparams.build_activation_layer(
                  name=layer_name))

        layer_name = '{}_2_Conv2d_{}_{}x{}_s2_{}'.format(
            base_from_layer, index, conv_kernel_size, conv_kernel_size,
            depth_fn(layer_depth))
        stride = 2
        padding = 'SAME'
        if use_explicit_padding:
          padding = 'VALID'
          # We define this function here while capturing the value of
          # conv_kernel_size, to avoid holding a reference to the loop variable
          # conv_kernel_size inside of a lambda function
          def fixed_padding(features, kernel_size=conv_kernel_size):
            return ops.fixed_padding(features, kernel_size)
          net.append(tf.keras.layers.Lambda(fixed_padding))
        # TODO(rathodv): Add some utilities to simplify the creation of
        # Depthwise & non-depthwise convolutions w/ normalization & activations
        if use_depthwise:
          net.append(tf.keras.layers.DepthwiseConv2D(
              [conv_kernel_size, conv_kernel_size],
              depth_multiplier=1,
              padding=padding,
              strides=stride,
              name=layer_name + '_depthwise_conv',
              **conv_hyperparams.params()))
          net.append(
              conv_hyperparams.build_batch_norm(
                  training=(is_training and not freeze_batchnorm),
                  name=layer_name + '_depthwise_batchnorm'))
          net.append(
              conv_hyperparams.build_activation_layer(
                  name=layer_name + '_depthwise'))

          net.append(tf.keras.layers.Conv2D(depth_fn(layer_depth), [1, 1],
                                            padding='SAME',
                                            strides=1,
                                            name=layer_name + '_conv',
                                            **conv_hyperparams.params()))
          net.append(
              conv_hyperparams.build_batch_norm(
                  training=(is_training and not freeze_batchnorm),
                  name=layer_name + '_batchnorm'))
          net.append(
              conv_hyperparams.build_activation_layer(
                  name=layer_name))

        else:
          net.append(tf.keras.layers.Conv2D(
              depth_fn(layer_depth),
              [conv_kernel_size, conv_kernel_size],
              padding=padding,
              strides=stride,
              name=layer_name + '_conv',
              **conv_hyperparams.params()))
          net.append(
              conv_hyperparams.build_batch_norm(
                  training=(is_training and not freeze_batchnorm),
                  name=layer_name + '_batchnorm'))
          net.append(
              conv_hyperparams.build_activation_layer(
                  name=layer_name))

      # Until certain bugs are fixed in checkpointable lists,
      # this net must be appended only once it's been filled with layers
      self.convolutions.append(net)