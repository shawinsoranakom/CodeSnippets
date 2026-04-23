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
      token_loss_init_value: float = 10.0,
      token_loss_beta: float = 0.995,
      token_keep_k: int = 256,
      token_allow_list: Tuple[int, ...] = (100, 101, 102, 103),
      token_deny_list: Tuple[int, ...] = (0,),
      initializer: _Initializer = tf_keras.initializers.TruncatedNormal(
          stddev=0.02),
      output_range: Optional[int] = None,
      embedding_width: Optional[int] = None,
      embedding_layer: Optional[tf_keras.layers.Layer] = None,
      norm_first: bool = False,
      with_dense_inputs: bool = False,
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

    # The first 999 tokens are special tokens such as [PAD], [CLS], [SEP].
    # We want to always mask [PAD], and always not to maks [CLS], [SEP].
    init_importance = tf.constant(token_loss_init_value, shape=(vocab_size))
    if token_allow_list:
      init_importance = tf.tensor_scatter_nd_update(
          tensor=init_importance,
          indices=[[x] for x in token_allow_list],
          updates=[1.0e4 for x in token_allow_list])
    if token_deny_list:
      init_importance = tf.tensor_scatter_nd_update(
          tensor=init_importance,
          indices=[[x] for x in token_deny_list],
          updates=[-1.0e4 for x in token_deny_list])
    self._token_importance_embed = layers.TokenImportanceWithMovingAvg(
        vocab_size=vocab_size,
        init_importance=init_importance,
        moving_average_beta=token_loss_beta)

    self._token_separator = layers.SelectTopK(top_k=token_keep_k)
    self._transformer_layers = []
    self._num_layers = num_layers
    self._attention_mask_layer = layers.SelfAttentionMask(
        name='self_attention_mask')
    for i in range(num_layers):
      layer = layers.TransformerEncoderBlock(
          num_attention_heads=num_attention_heads,
          inner_dim=inner_dim,
          inner_activation=inner_activation,
          output_dropout=output_dropout,
          attention_dropout=attention_dropout,
          norm_first=norm_first,
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
        'inner_activation': tf_keras.activations.serialize(activation),
        'output_dropout': output_dropout,
        'attention_dropout': attention_dropout,
        'token_loss_init_value': token_loss_init_value,
        'token_loss_beta': token_loss_beta,
        'token_keep_k': token_keep_k,
        'token_allow_list': token_allow_list,
        'token_deny_list': token_deny_list,
        'initializer': tf_keras.initializers.serialize(initializer),
        'output_range': output_range,
        'embedding_width': embedding_width,
        'embedding_layer': embedding_layer,
        'norm_first': norm_first,
        'with_dense_inputs': with_dense_inputs,
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