def __init__(
      self,
      vocab_size: int,
      hidden_size: int = 768,
      num_layers: int = 12,
      num_attention_heads: int = 12,
      max_sequence_length: int = 512,
      type_vocab_size: int = 16,
      inner_dim: int = 3072,
      inner_activation: _Activation = _approx_gelu,
      output_dropout: float = 0.1,
      attention_dropout: float = 0.1,
      pool_type: str = _MAX,
      pool_stride: Union[int, Sequence[Union[int, float]]] = 2,
      unpool_length: int = 0,
      initializer: _Initializer = tf_keras.initializers.TruncatedNormal(
          stddev=0.02
      ),
      output_range: Optional[int] = None,
      embedding_width: Optional[int] = None,
      embedding_layer: Optional[tf_keras.layers.Layer] = None,
      norm_first: bool = False,
      transformer_cls: Union[
          str, tf_keras.layers.Layer
      ] = layers.TransformerEncoderBlock,
      share_rezero: bool = False,
      append_dense_inputs: bool = False,
      **kwargs
  ):
    super().__init__(**kwargs)

    if output_range is not None:
      logging.warning('`output_range` is available as an argument for `call()`.'
                      'The `output_range` as __init__ argument is deprecated.')

    activation = tf_keras.activations.get(inner_activation)
    initializer = tf_keras.initializers.get(initializer)

    if embedding_width is None:
      embedding_width = hidden_size

    if embedding_layer is None:
      self._embedding_layer = layers.OnDeviceEmbedding(
          vocab_size=vocab_size,
          embedding_width=embedding_width,
          initializer=tf_utils.clone_initializer(initializer),
          name='word_embeddings')
    else:
      self._embedding_layer = embedding_layer

    self._position_embedding_layer = layers.PositionEmbedding(
        initializer=tf_utils.clone_initializer(initializer),
        max_length=max_sequence_length,
        name='position_embedding')

    self._type_embedding_layer = layers.OnDeviceEmbedding(
        vocab_size=type_vocab_size,
        embedding_width=embedding_width,
        initializer=tf_utils.clone_initializer(initializer),
        use_one_hot=True,
        name='type_embeddings')

    self._embedding_norm_layer = tf_keras.layers.LayerNormalization(
        name='embeddings/layer_norm', axis=-1, epsilon=1e-12, dtype=tf.float32)

    self._embedding_dropout = tf_keras.layers.Dropout(
        rate=output_dropout, name='embedding_dropout')

    # We project the 'embedding' output to 'hidden_size' if it is not already
    # 'hidden_size'.
    self._embedding_projection = None
    if embedding_width != hidden_size:
      self._embedding_projection = tf_keras.layers.EinsumDense(
          '...x,xy->...y',
          output_shape=hidden_size,
          bias_axes='y',
          kernel_initializer=tf_utils.clone_initializer(initializer),
          name='embedding_projection')

    self._transformer_layers = []
    self._attention_mask_layer = layers.SelfAttentionMask(
        name='self_attention_mask')
    # Will raise an error if the string is not supported.
    if isinstance(transformer_cls, str):
      transformer_cls = _str2transformer_cls[transformer_cls]
    self._num_layers = num_layers
    for i in range(num_layers):
      layer = transformer_cls(
          num_attention_heads=num_attention_heads,
          intermediate_size=inner_dim,
          inner_dim=inner_dim,
          intermediate_activation=inner_activation,
          inner_activation=inner_activation,
          output_dropout=output_dropout,
          attention_dropout=attention_dropout,
          norm_first=norm_first,
          kernel_initializer=tf_utils.clone_initializer(initializer),
          share_rezero=share_rezero,
          name='transformer/layer_%d' % i)
      self._transformer_layers.append(layer)

    self._pooler_layer = tf_keras.layers.Dense(
        units=hidden_size,
        activation='tanh',
        kernel_initializer=tf_utils.clone_initializer(initializer),
        name='pooler_transform')
    if isinstance(pool_stride, int):
      # TODO(b/197133196): Pooling layer can be shared.
      pool_strides = [pool_stride] * num_layers
    else:
      if len(pool_stride) != num_layers:
        raise ValueError('Lengths of pool_stride and num_layers are not equal.')
      pool_strides = pool_stride

    is_fractional_pooling = False in [
        (1.0 * pool_stride).is_integer() for pool_stride in pool_strides
    ]
    if is_fractional_pooling and pool_type in [_MAX, _AVG]:
      raise ValueError(
          'Fractional pooling is only supported for'
          ' `pool_type`=`truncated_average`'
      )

    # TODO(crickwu): explore tf_keras.layers.serialize method.
    if pool_type == _MAX:
      pool_cls = tf_keras.layers.MaxPooling1D
    elif pool_type == _AVG:
      pool_cls = tf_keras.layers.AveragePooling1D
    elif pool_type == _TRUNCATED_AVG:
      # TODO(b/203665205): unpool_length should be implemented.
      if unpool_length != 0:
        raise ValueError('unpool_length is not supported by truncated_avg now.')
    else:
      raise ValueError('pool_type not supported.')

    if pool_type in (_MAX, _AVG):
      self._att_input_pool_layers = []
      for layer_pool_stride in pool_strides:
        att_input_pool_layer = pool_cls(
            pool_size=layer_pool_stride,
            strides=layer_pool_stride,
            padding='same',
            name='att_input_pool_layer')
        self._att_input_pool_layers.append(att_input_pool_layer)

    self._max_sequence_length = max_sequence_length
    self._pool_strides = pool_strides  # This is a list here.
    self._unpool_length = unpool_length
    self._pool_type = pool_type
    self._append_dense_inputs = append_dense_inputs

    self._config = {
        'vocab_size': vocab_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'num_attention_heads': num_attention_heads,
        'max_sequence_length': max_sequence_length,
        'type_vocab_size': type_vocab_size,
        'inner_dim': inner_dim,
        'inner_activation': tf_keras.activations.serialize(activation),
        'output_dropout': output_dropout,
        'attention_dropout': attention_dropout,
        'initializer': tf_keras.initializers.serialize(initializer),
        'output_range': output_range,
        'embedding_width': embedding_width,
        'embedding_layer': embedding_layer,
        'norm_first': norm_first,
        'pool_type': pool_type,
        'pool_stride': pool_stride,
        'unpool_length': unpool_length,
        'transformer_cls': _transformer_cls2str.get(
            transformer_cls, str(transformer_cls)
        ),
    }

    self.inputs = dict(
        input_word_ids=tf_keras.Input(shape=(None,), dtype=tf.int32),
        input_mask=tf_keras.Input(shape=(None,), dtype=tf.int32),
        input_type_ids=tf_keras.Input(shape=(None,), dtype=tf.int32))