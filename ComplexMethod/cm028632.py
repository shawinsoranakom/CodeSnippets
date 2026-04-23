def mobilenet_edgetpu_v2(image_input: tf_keras.layers.Input,
                         config: ModelConfig):  # pytype: disable=invalid-annotation  # typed-keras
  """Creates a MobilenetEdgeTPUV2 graph given the model parameters.

  This function is wrapped by the `MobilenetEdgeTPUV2` class to make a
  tf_keras.Model.

  Args:
    image_input: the input batch of images
    config: the model config

  Returns:
    The output of classification model or if backbone is needed, dictionary with
    backbone feature levels.
  """
  depth_coefficient = config.depth_coefficient
  blocks = config.blocks
  stem_base_filters = config.stem_base_filters
  stem_kernel_size = config.stem_kernel_size
  top_base_filters = config.top_base_filters
  activation = tf_utils.get_activation(config.activation)
  dropout_rate = config.dropout_rate
  drop_connect_rate = config.drop_connect_rate
  conv_kernel_initializer = (
      config.conv_kernel_initializer if config.conv_kernel_initializer
      is not None else CONV_KERNEL_INITIALIZER)
  dense_kernel_initializer = (
      config.dense_kernel_initializer if config.dense_kernel_initializer
      is not None else DENSE_KERNEL_INITIALIZER)
  num_classes = config.num_classes
  input_channels = config.input_channels
  rescale_input = config.rescale_input
  data_format = tf_keras.backend.image_data_format()
  dtype = config.dtype
  weight_decay = config.weight_decay

  x = image_input
  if data_format == 'channels_first':
    # Happens on GPU/TPU if available.
    x = tf_keras.layers.Permute((3, 1, 2))(x)
  if rescale_input:
    x = common_modules.normalize_images(
        x, num_channels=input_channels, dtype=dtype, data_format=data_format)

  # Build stem
  x = conv2d_block(
      inputs=x,
      conv_filters=round_filters(stem_base_filters, config),
      config=config,
      kernel_size=[stem_kernel_size, stem_kernel_size],
      strides=[2, 2],
      activation=activation,
      kernel_initializer=conv_kernel_initializer,
      name='stem')

  # Build blocks
  num_blocks_total = sum(block.num_repeat for block in blocks)
  block_num = 0

  backbone_levels = []
  for stack_idx, block in enumerate(blocks):
    is_reduction = False
    assert block.num_repeat > 0
    # Update block input and output filters based on depth multiplier
    block = block.replace(
        input_filters=round_filters(block.input_filters, config),
        output_filters=round_filters(block.output_filters, config),
        num_repeat=round_repeats(block.num_repeat, depth_coefficient))

    if stack_idx == 0:
      backbone_levels.append(x)
    elif (stack_idx == len(blocks) - 1) or (blocks[stack_idx + 1].strides
                                            == (2, 2)):
      is_reduction = True
    # The first block needs to take care of stride and filter size increase
    drop_rate = drop_connect_rate * float(block_num) / num_blocks_total
    config = config.replace(drop_connect_rate=drop_rate)
    block_prefix = 'stack_{}/block_0/'.format(stack_idx)
    x = _MbConvBlock(block, config, block_prefix)(x)
    block_num += 1
    if block.num_repeat > 1:
      block = block.replace(
          input_filters=block.output_filters,
          strides=[1, 1]
      )

      for block_idx in range(block.num_repeat - 1):
        drop_rate = drop_connect_rate * float(block_num) / num_blocks_total
        config = config.replace(drop_connect_rate=drop_rate)
        block_prefix = 'stack_{}/block_{}/'.format(stack_idx, block_idx + 1)
        x = _MbConvBlock(block, config, prefix=block_prefix)(x)
        block_num += 1
    if is_reduction:
      backbone_levels.append(x)

  if config.backbone_only:
    return backbone_levels
  # Build top
  x = conv2d_block(
      inputs=x,
      conv_filters=round_filters(top_base_filters, config),
      config=config,
      activation=activation,
      kernel_initializer=conv_kernel_initializer,
      name='top')

  # Build classifier
  pool_size = (x.shape.as_list()[1], x.shape.as_list()[2])
  x = tf_keras.layers.AveragePooling2D(pool_size, name='top_pool')(x)
  if dropout_rate and dropout_rate > 0:
    x = tf_keras.layers.Dropout(dropout_rate, name='top_dropout')(x)
  x = tf_keras.layers.Conv2D(
      num_classes,
      1,
      kernel_initializer=dense_kernel_initializer,
      kernel_regularizer=tf_keras.regularizers.l2(weight_decay),
      bias_regularizer=tf_keras.regularizers.l2(weight_decay),
      name='logits')(
          x)
  x = tf_keras.layers.Activation('softmax', name='probs')(x)
  x = tf.squeeze(x, axis=[1, 2])

  return x