def __init__(self,
               block: BlockConfig,
               config: ModelConfig,
               prefix: Optional[str] = None):
    """Mobile Inverted Residual Bottleneck.

    Args:
      block: BlockConfig, arguments to create a Block
      config: ModelConfig, a set of model parameters
      prefix: prefix for naming all layers
    """
    use_se = config.use_se
    activation = tf_utils.get_activation(config.activation)
    drop_connect_rate = config.drop_connect_rate
    data_format = tf_keras.backend.image_data_format()
    use_depthwise = block.conv_type == 'depthwise'
    use_groupconv = block.conv_type == 'group'
    prefix = prefix or ''
    self.name = prefix
    conv_kernel_initializer = (
        config.conv_kernel_initializer if config.conv_kernel_initializer
        is not None else CONV_KERNEL_INITIALIZER)

    filters = block.input_filters * block.expand_ratio

    self.expand_block: List[tf_keras.layers.Layer] = []
    self.squeeze_excitation: List[tf_keras.layers.Layer] = []
    self.project_block: List[tf_keras.layers.Layer] = []

    if block.fused_project:
      raise NotImplementedError('Fused projection is not supported.')

    if block.fused_expand and block.expand_ratio != 1:
      # If we use fused mbconv, fuse expansion with the main kernel.
      # If conv_type is depthwise we still fuse it to a full conv.
      if use_groupconv:
        self.expand_block.append(groupconv2d_block(
            filters,
            config,
            kernel_size=block.kernel_size,
            strides=block.strides,
            group_size=block.group_size,
            activation=activation,
            name=prefix + 'fused'))
      else:
        self.expand_block.extend(
            conv2d_block_as_layers(
                conv_filters=filters,
                config=config,
                kernel_size=block.kernel_size,
                strides=block.strides,
                activation=activation,
                kernel_initializer=conv_kernel_initializer,
                name=prefix + 'fused'))
    else:
      if block.expand_ratio != 1:
        # Expansion phase with a pointwise conv
        self.expand_block.extend(
            conv2d_block_as_layers(
                conv_filters=filters,
                config=config,
                kernel_size=(1, 1),
                activation=activation,
                kernel_initializer=conv_kernel_initializer,
                name=prefix + 'expand'))

      # Main kernel, after the expansion (if applicable, i.e. not fused).
      if use_depthwise:
        self.expand_block.extend(conv2d_block_as_layers(
            conv_filters=filters,
            config=config,
            kernel_size=block.kernel_size,
            strides=block.strides,
            activation=activation,
            kernel_initializer=conv_kernel_initializer,
            depthwise=True,
            name=prefix + 'depthwise'))
      elif use_groupconv:
        self.expand_block.append(groupconv2d_block(
            conv_filters=filters,
            config=config,
            kernel_size=block.kernel_size,
            strides=block.strides,
            group_size=block.group_size,
            activation=activation,
            name=prefix + 'group'))

    # Squeeze and Excitation phase
    if use_se:
      assert block.se_ratio is not None
      assert 0 < block.se_ratio <= 1
      num_reduced_filters = max(1, int(
          block.input_filters * block.se_ratio
      ))

      if data_format == 'channels_first':
        se_shape = (filters, 1, 1)
      else:
        se_shape = (1, 1, filters)

      self.squeeze_excitation.append(
          tf_keras.layers.GlobalAveragePooling2D(name=prefix + 'se_squeeze'))
      self.squeeze_excitation.append(
          tf_keras.layers.Reshape(se_shape, name=prefix + 'se_reshape'))
      self.squeeze_excitation.extend(
          conv2d_block_as_layers(
              conv_filters=num_reduced_filters,
              config=config,
              use_bias=True,
              use_batch_norm=False,
              activation=activation,
              kernel_initializer=conv_kernel_initializer,
              name=prefix + 'se_reduce'))
      self.squeeze_excitation.extend(
          conv2d_block_as_layers(
              conv_filters=filters,
              config=config,
              use_bias=True,
              use_batch_norm=False,
              activation='sigmoid',
              kernel_initializer=conv_kernel_initializer,
              name=prefix + 'se_expand'))

    # Output phase
    self.project_block.extend(
        conv2d_block_as_layers(
            conv_filters=block.output_filters,
            config=config,
            activation=None,
            kernel_initializer=conv_kernel_initializer,
            name=prefix + 'project'))

    # Add identity so that quantization-aware training can insert quantization
    # ops correctly.
    self.project_block.append(
        tf_keras.layers.Activation('linear', name=prefix + 'id'))

    self.has_skip_add = False
    if (block.id_skip
        and all(s == 1 for s in block.strides)
        and block.input_filters == block.output_filters):
      self.has_skip_add = True
      if drop_connect_rate and drop_connect_rate > 0:
        # Apply dropconnect
        # The only difference between dropout and dropconnect in TF is scaling
        # by drop_connect_rate during training. See:
        # https://github.com/keras-team/keras/pull/9898#issuecomment-380577612
        self.project_block.append(
            tf_keras.layers.Dropout(
                drop_connect_rate,
                noise_shape=(None, 1, 1, 1),
                name=prefix + 'drop'))