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
      initializer: _Initializer = tf_keras.initializers.TruncatedNormal(
          stddev=0.02),
      output_range: Optional[int] = None,
      embedding_width: Optional[int] = None,
      embedding_layer: Optional[tf_keras.layers.Layer] = None,
      norm_first: bool = False,
      with_dense_inputs: bool = False,
      return_attention_scores: bool = False,
      return_word_embeddings: bool = False,
      **kwargs):
    # Pops kwargs that are used in V1 implementation.
    if 'dict_outputs' in kwargs:
      kwargs.pop('dict_outputs')
    if 'return_all_encoder_outputs' in kwargs:
      kwargs.pop('return_all_encoder_outputs')
    if 'intermediate_size' in kwargs:
      inner_dim = kwargs.pop('intermediate_size')
    if 'activation' in kwargs:
      inner_activation = kwargs.pop('activation')
    if 'dropout_rate' in kwargs:
      output_dropout = kwargs.pop('dropout_rate')
    if 'attention_dropout_rate' in kwargs:
      attention_dropout = kwargs.pop('attention_dropout_rate')
    super().__init__(**kwargs)

    self._output_range = output_range

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
    self._num_layers = num_layers
    for i in range(num_layers):
      layer = layers.TransformerEncoderBlock(
          num_attention_heads=num_attention_heads,
          inner_dim=inner_dim,
          inner_activation=inner_activation,
          output_dropout=output_dropout,
          attention_dropout=attention_dropout,
          norm_first=norm_first,
          return_attention_scores=return_attention_scores,
          kernel_initializer=tf_utils.clone_initializer(initializer),
          name='transformer/layer_%d' % i)
      self._transformer_layers.append(layer)

    self._pooler_layer = tf_keras.layers.Dense(
        units=hidden_size,
        activation='tanh',
        kernel_initializer=tf_utils.clone_initializer(initializer),
        name='pooler_transform')

    self._config = {
        'vocab_size': vocab_size,
        'hidden_size': hidden_size,
        'num_layers': num_layers,
        'num_attention_heads': num_attention_heads,
        'max_sequence_length': max_sequence_length,
        'type_vocab_size': type_vocab_size,
        'inner_dim': inner_dim,
        'inner_activation': tf_utils.serialize_activation(
            activation, use_legacy_format=True
        ),
        'output_dropout': output_dropout,
        'attention_dropout': attention_dropout,
        'initializer': tf_utils.serialize_initializer(
            initializer, use_legacy_format=True
        ),
        'output_range': output_range,
        'embedding_width': embedding_width,
        'embedding_layer': embedding_layer,
        'norm_first': norm_first,
        'with_dense_inputs': with_dense_inputs,
        'return_attention_scores': return_attention_scores,
        'return_word_embeddings': return_word_embeddings,
    }
    if with_dense_inputs:
      self.inputs = dict(
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
          input_word_ids=tf_keras.Input(shape=(None,), dtype=tf.int32),
          input_mask=tf_keras.Input(shape=(None,), dtype=tf.int32),
          input_type_ids=tf_keras.Input(shape=(None,), dtype=tf.int32))