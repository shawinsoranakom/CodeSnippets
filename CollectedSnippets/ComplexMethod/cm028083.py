def __init__(self,
               data_format,
               name='',
               include_top=True,
               pooling=None,
               block3_strides=False,
               average_pooling=True,
               classes=1000,
               gem_power=3.0,
               embedding_layer=False,
               embedding_layer_dim=2048):
    super(ResNet50, self).__init__(name=name)

    valid_channel_values = ('channels_first', 'channels_last')
    if data_format not in valid_channel_values:
      raise ValueError('Unknown data_format: %s. Valid values: %s' %
                       (data_format, valid_channel_values))
    self.include_top = include_top
    self.block3_strides = block3_strides
    self.average_pooling = average_pooling
    self.pooling = pooling

    def conv_block(filters, stage, block, strides=(2, 2)):
      return _ConvBlock(
          3,
          filters,
          stage=stage,
          block=block,
          data_format=data_format,
          strides=strides)

    def id_block(filters, stage, block):
      return _IdentityBlock(
          3, filters, stage=stage, block=block, data_format=data_format)

    self.conv1 = layers.Conv2D(
        64, (7, 7),
        strides=(2, 2),
        data_format=data_format,
        padding='same',
        name='conv1')
    bn_axis = 1 if data_format == 'channels_first' else 3
    self.bn_conv1 = layers.BatchNormalization(axis=bn_axis, name='bn_conv1')
    self.max_pool = layers.MaxPooling2D((3, 3),
                                        strides=(2, 2),
                                        data_format=data_format)

    self.l2a = conv_block([64, 64, 256], stage=2, block='a', strides=(1, 1))
    self.l2b = id_block([64, 64, 256], stage=2, block='b')
    self.l2c = id_block([64, 64, 256], stage=2, block='c')

    self.l3a = conv_block([128, 128, 512], stage=3, block='a')
    self.l3b = id_block([128, 128, 512], stage=3, block='b')
    self.l3c = id_block([128, 128, 512], stage=3, block='c')
    self.l3d = id_block([128, 128, 512], stage=3, block='d')

    self.l4a = conv_block([256, 256, 1024], stage=4, block='a')
    self.l4b = id_block([256, 256, 1024], stage=4, block='b')
    self.l4c = id_block([256, 256, 1024], stage=4, block='c')
    self.l4d = id_block([256, 256, 1024], stage=4, block='d')
    self.l4e = id_block([256, 256, 1024], stage=4, block='e')
    self.l4f = id_block([256, 256, 1024], stage=4, block='f')

    # Striding layer that can be used on top of block3 to produce feature maps
    # with the same resolution as the TF-Slim implementation.
    if self.block3_strides:
      self.subsampling_layer = layers.MaxPooling2D((1, 1),
                                                   strides=(2, 2),
                                                   data_format=data_format)
      self.l5a = conv_block([512, 512, 2048],
                            stage=5,
                            block='a',
                            strides=(1, 1))
    else:
      self.l5a = conv_block([512, 512, 2048], stage=5, block='a')
    self.l5b = id_block([512, 512, 2048], stage=5, block='b')
    self.l5c = id_block([512, 512, 2048], stage=5, block='c')

    self.avg_pool = layers.AveragePooling2D((7, 7),
                                            strides=(7, 7),
                                            data_format=data_format)

    if self.include_top:
      self.flatten = layers.Flatten()
      self.fc1000 = layers.Dense(classes, name='fc1000')
    else:
      reduction_indices = [1, 2] if data_format == 'channels_last' else [2, 3]
      reduction_indices = tf.constant(reduction_indices)
      if pooling == 'avg':
        self.global_pooling = functools.partial(
            tf.reduce_mean, axis=reduction_indices, keepdims=False)
      elif pooling == 'max':
        self.global_pooling = functools.partial(
            tf.reduce_max, axis=reduction_indices, keepdims=False)
      elif pooling == 'gem':
        logging.info('Adding GeMPooling layer with power %f', gem_power)
        self.global_pooling = functools.partial(
            pooling_layers.gem, axis=reduction_indices, power=gem_power)
      else:
        self.global_pooling = None
      if embedding_layer:
        logging.info('Adding embedding layer with dimension %d',
                     embedding_layer_dim)
        self.embedding_layer = layers.Dense(
            embedding_layer_dim, name='embedding_layer')
      else:
        self.embedding_layer = None