def __init__(
      self,
      vocab_size: int,
      hidden_size: int = 768,
      num_layers: int = 12,
      mixing_mechanism: layers.MixingMechanism = layers.MixingMechanism.FOURIER,
      use_fft: bool = False,
      attention_layers: Sequence[int] = (),
      num_attention_heads: int = 12,
      max_sequence_length: int = 512,
      type_vocab_size: int = 16,
      inner_dim: int = 3072,
      inner_activation: _Activation = _approx_gelu,
      output_dropout: float = 0.1,
      attention_dropout: float = 0.1,
      initializer: _Initializer = tf_keras.initializers.TruncatedNormal(
          stddev=0.02),
      output_range: Optional[int] = None,
      embedding_width: Optional[int] = None,
      embedding_layer: Optional[tf_keras.layers.Layer] = None,
      norm_first: bool = False,
      with_dense_inputs: bool = False,
      **kwargs):
    super().__init__(**kwargs)

    activation = tf_keras.activations.get(inner_activation)
    initializer = tf_keras.initializers.get(initializer)

    if embedding_width is None:
      embedding_width = hidden_size

    self._config = {
        'vocab_size': vocab_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'mixing_mechanism': mixing_mechanism,
        'use_fft': use_fft,
        'attention_layers': attention_layers,
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
        'with_dense_inputs': with_dense_inputs,
    }

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
    for layer in range(num_layers):
      if layer in attention_layers:
        mixing_layer = layers.MultiHeadAttention(
            num_heads=num_attention_heads,
            key_dim=int(hidden_size // num_attention_heads),
            dropout=attention_dropout,
            use_bias=True,
            kernel_initializer=tf_utils.clone_initializer(initializer),
            name='self_attention',
        )
      else:
        mixing_layer = self._init_mixing_sublayer(layer)

      block = layers.TransformerScaffold(
          num_attention_heads=num_attention_heads,
          inner_dim=inner_dim,
          inner_activation=inner_activation,
          attention_cls=mixing_layer,
          feedforward_cls=None,  # Fallback to default FeedForward class
          output_dropout=output_dropout,
          attention_dropout=attention_dropout,
          norm_first=norm_first,
          output_range=output_range if layer == num_layers - 1 else None,
          kernel_initializer=tf_utils.clone_initializer(initializer),
          name='transformer/layer_%d' % layer)
      self._transformer_layers.append(block)

    self._attention_mask_layer = layers.SelfAttentionMask(
        name='self_attention_mask')

    self._pooler_layer = tf_keras.layers.Dense(
        units=hidden_size,
        activation='tanh',
        kernel_initializer=tf_utils.clone_initializer(initializer),
        name='pooler_transform')

    if with_dense_inputs:
      self.inputs = dict(
          # The total length of token ids and dense inputs still has to be
          # max_sequence_length. It is checked in call().
          input_word_ids=tf_keras.Input(shape=(None,), dtype=tf.int32),
          input_mask=tf_keras.Input(shape=(None,), dtype=tf.int32),
          input_type_ids=tf_keras.Input(shape=(None,), dtype=tf.int32),
          dense_inputs=tf_keras.Input(
              shape=(None, embedding_width), dtype=tf.float32),
          dense_mask=tf_keras.Input(shape=(None,), dtype=tf.int32),
          dense_type_ids=tf_keras.Input(shape=(None,), dtype=tf.int32),
      )

    else:
      self.inputs = dict(
          input_word_ids=tf_keras.Input(
              shape=(max_sequence_length,), dtype=tf.int32),
          input_mask=tf_keras.Input(
              shape=(max_sequence_length,), dtype=tf.int32),
          input_type_ids=tf_keras.Input(
              shape=(max_sequence_length,), dtype=tf.int32))
    self._max_sequence_length = max_sequence_length