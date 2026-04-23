def build(self, input_shape: tf.TensorShape) -> None:
    if self._norm_type == 'layer_norm':
      bn_class = functools.partial(
          tf_keras.layers.LayerNormalization, epsilon=self._ln_epsilon
      )
    elif self._norm_type == 'batch_norm':
      bn_class = functools.partial(
          tf_keras.layers.BatchNormalization,
          momentum=self._bn_momentum,
          epsilon=self._bn_epsilon,
      )
    elif self._norm_type == 'sync_batch_norm':
      bn_class = functools.partial(
          tf_keras.layers.BatchNormalization,
          momentum=self._bn_momentum,
          epsilon=self._bn_epsilon,
          synchronized=True,
      )
    else:
      raise ValueError(f'Unsupported norm_type {self._norm_type}.')

    _, self.height, self.width, _ = input_shape.as_list()
    logging.info(
        f'Build backbone with input size: ({self.height}, {self.width}).'
    )

    # Stem
    stem_layers = []
    for i, _ in enumerate(self._stem_hsize):
      conv_layer = tf_keras.layers.Conv2D(
          filters=self._stem_hsize[i],
          kernel_size=self._kernel_size,
          strides=2 if i == 0 else 1,
          padding='same',
          data_format=self._data_format,
          kernel_initializer=self._kernel_initializer,
          bias_initializer=self._bias_initializer,
          use_bias=True,
          name='conv_{}'.format(i),
      )
      stem_layers.append(conv_layer)
      if i < len(self._stem_hsize) - 1:
        stem_layers.append(bn_class(name='norm_{}'.format(i)))
        stem_layers.append(
            tf_keras.layers.Activation(
                ops.get_act_fn(self._activation), name=f'act_{i}'
            )
        )
    self._stem = tf_keras.Sequential(layers=stem_layers, name='stem')

    # Backbone
    self._blocks = []
    total_num_blocks = sum(self._num_blocks)
    bid = 0
    for i, _ in enumerate(self._block_type):
      self._blocks.append([])
      for j in range(self._num_blocks[i]):
        # block name
        block_name = f'block_{i:0>2d}_{j:0>2d}'

        ##### Update per-block config
        # No pooling if not the first block in the stage
        if j == 0:
          pool_stride = self._pool_stride
        else:
          pool_stride = 1

        # anneal the survival prob
        survival_prob = self._survival_prob
        if survival_prob and self._survival_prob_anneal:
          drop_rate = 1.0 - survival_prob
          survival_prob = 1.0 - drop_rate * bid / total_num_blocks
          logging.info(
              '[%02d/%02d] %s survival_prob: %.4f',
              bid,
              total_num_blocks,
              block_name,
              survival_prob,
          )

        ##### Init block
        if self._block_type[i] == 'tfm':
          block = layers.TransformerBlock(
              hidden_size=self._hidden_size[i],
              head_size=self._head_size,
              input_origin_height=self.height,
              input_origin_width=self.width,
              num_heads=self._num_heads,
              expansion_rate=self._expansion_rate,
              activation=self._activation,
              pool_type=self._pool_type,
              pool_stride=pool_stride,
              dropatt=self._dropatt,
              dropout=self._dropout,
              rel_attn_type=self._rel_attn_type,
              scale_ratio=self._scale_ratio,
              survival_prob=survival_prob,
              ln_epsilon=self._ln_epsilon,
              ln_dtype=self._ln_dtype,
              kernel_initializer=self._kernel_initializer,
              bias_initializer=self._bias_initializer,
              name=block_name,
          )
        elif self._block_type[i] == 'mbconv':
          assert self._pool_type in ['2d:max', '2d:avg'], (
              'Invalid pool_type %s for MBConv block' % self._pool_type
          )
          pool_type = self._pool_type.split(':')[-1]
          block = layers.MBConvBlock(
              hidden_size=self._hidden_size[i],
              downsample_loc=self._downsample_loc,
              data_format=self._data_format,
              kernel_size=self._kernel_size,
              expansion_rate=self._expansion_rate,
              se_ratio=self._se_ratio,
              activation=self._activation,
              pool_type=pool_type,
              pool_stride=pool_stride,
              dropcnn=self._dropcnn,
              survival_prob=survival_prob,
              norm_type=self._norm_type,
              bn_epsilon=self._bn_epsilon,
              bn_momentum=self._bn_momentum,
              kernel_initializer=self._kernel_initializer,
              bias_initializer=self._bias_initializer,
              name=block_name,
          )
        elif self._block_type[i] == 'maxvit':
          block = MaxViTBlock(
              hidden_size=self._hidden_size[i],
              head_size=self._head_size,
              window_size=self._window_size,
              grid_size=self._grid_size,
              num_heads=self._num_heads,
              downsample_loc=self._downsample_loc,
              data_format=self._data_format,
              kernel_size=self._kernel_size,
              expansion_rate=self._expansion_rate,
              se_ratio=self._se_ratio,
              activation=self._activation,
              pool_type=self._pool_type,
              pool_stride=pool_stride,
              dropcnn=self._dropcnn,
              dropatt=self._dropatt,
              dropout=self._dropout,
              rel_attn_type=self._rel_attn_type,
              scale_ratio=self._scale_ratio,
              survival_prob=survival_prob,
              ln_epsilon=self._ln_epsilon,
              ln_dtype=self._ln_dtype,
              norm_type=self._norm_type,
              bn_epsilon=self._bn_epsilon,
              bn_momentum=self._bn_momentum,
              kernel_initializer=self._kernel_initializer,
              bias_initializer=self._bias_initializer,
              name=block_name,
          )
        else:
          raise ValueError(f'Unsupported block_type {self._block_type[i]}')
        self._blocks[-1].append(block)
        bid += 1

    if self._representation_size and self._representation_size > 0:
      self._dense = tf_keras.layers.Dense(
          self._representation_size, name='pre_logits')
      if self._add_gap_layer_norm:
        self._final_layer_norm = tf_keras.layers.LayerNormalization(
            epsilon=self._ln_epsilon, name='final_layer_norm')