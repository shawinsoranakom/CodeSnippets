def efficientnet(image_input: tf_keras.layers.Input, config: ModelConfig):  # pytype: disable=invalid-annotation  # typed-keras
  """Creates an EfficientNet graph given the model parameters.

  This function is wrapped by the `EfficientNet` class to make a tf_keras.Model.

  Args:
    image_input: the input batch of images
    config: the model config

  Returns:
    the output of efficientnet
  """
  depth_coefficient = config.depth_coefficient
  blocks = config.blocks
  stem_base_filters = config.stem_base_filters
  top_base_filters = config.top_base_filters
  activation = tf_utils.get_activation(config.activation)
  dropout_rate = config.dropout_rate
  drop_connect_rate = config.drop_connect_rate
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
    x = preprocessing.normalize_images(
        x, num_channels=input_channels, dtype=dtype, data_format=data_format)

  # Build stem
  x = conv2d_block(
      x,
      round_filters(stem_base_filters, config),
      config,
      kernel_size=[3, 3],
      strides=[2, 2],
      activation=activation,
      name='stem')

  # Build blocks
  num_blocks_total = sum(
      round_repeats(block.num_repeat, depth_coefficient) for block in blocks)
  block_num = 0

  for stack_idx, block in enumerate(blocks):
    assert block.num_repeat > 0
    # Update block input and output filters based on depth multiplier
    block = block.replace(
        input_filters=round_filters(block.input_filters, config),
        output_filters=round_filters(block.output_filters, config),
        num_repeat=round_repeats(block.num_repeat, depth_coefficient))

    # The first block needs to take care of stride and filter size increase
    drop_rate = drop_connect_rate * float(block_num) / num_blocks_total
    config = config.replace(drop_connect_rate=drop_rate)
    block_prefix = 'stack_{}/block_0/'.format(stack_idx)
    x = mb_conv_block(x, block, config, block_prefix)
    block_num += 1
    if block.num_repeat > 1:
      block = block.replace(input_filters=block.output_filters, strides=[1, 1])

      for block_idx in range(block.num_repeat - 1):
        drop_rate = drop_connect_rate * float(block_num) / num_blocks_total
        config = config.replace(drop_connect_rate=drop_rate)
        block_prefix = 'stack_{}/block_{}/'.format(stack_idx, block_idx + 1)
        x = mb_conv_block(x, block, config, prefix=block_prefix)
        block_num += 1

  # Build top
  x = conv2d_block(
      x,
      round_filters(top_base_filters, config),
      config,
      activation=activation,
      name='top')

  # Build classifier
  x = tf_keras.layers.GlobalAveragePooling2D(name='top_pool')(x)
  if dropout_rate and dropout_rate > 0:
    x = tf_keras.layers.Dropout(dropout_rate, name='top_dropout')(x)
  x = tf_keras.layers.Dense(
      num_classes,
      kernel_initializer=DENSE_KERNEL_INITIALIZER,
      kernel_regularizer=tf_keras.regularizers.l2(weight_decay),
      bias_regularizer=tf_keras.regularizers.l2(weight_decay),
      name='logits')(
          x)
  x = tf_keras.layers.Activation('softmax', name='probs')(x)

  return x