def __init__(
      self,
      vocab_size,
      hidden_size=768,  # FIXME: hidden_size per head should be even!
      num_layers=12,
      num_attention_heads=12,
      max_sequence_length=512,
      type_vocab_size=16,
      inner_dim=3072,
      inner_activation=lambda x: tf_keras.activations.gelu(x, approximate=True),
      output_dropout=0.1,
      attention_dropout=0.1,
      initializer=tf_keras.initializers.TruncatedNormal(stddev=0.02),
      output_range=None,
      embedding_width=None,
      embedding_layer=None,
      norm_first=False,
      **kwargs):
    if 'intermediate_size' in kwargs:
      inner_dim = kwargs['intermediate_size']
      del kwargs['intermediate_size']
    if 'activation' in kwargs:
      inner_activation = kwargs['activation']
      del kwargs['activation']
    if 'dropout_rate' in kwargs:
      output_dropout = kwargs['dropout_rate']
      del kwargs['dropout_rate']
    if 'attention_dropout_rate' in kwargs:
      attention_dropout = kwargs['attention_dropout_rate']
      del kwargs['attention_dropout_rate']

    activation = tf_keras.activations.get(inner_activation)
    initializer = tf_keras.initializers.get(initializer)

    word_ids = tf_keras.layers.Input(
        shape=(None,), dtype=tf.int32, name='input_word_ids')
    mask = tf_keras.layers.Input(
        shape=(None,), dtype=tf.int32, name='input_mask')
    type_ids = tf_keras.layers.Input(
        shape=(None,), dtype=tf.int32, name='input_type_ids')

    if embedding_width is None:
      embedding_width = hidden_size

    if embedding_layer is None:
      embedding_layer_inst = layers.on_device_embedding.OnDeviceEmbedding(
          vocab_size=vocab_size,
          embedding_width=embedding_width,
          initializer=tf_utils.clone_initializer(initializer),
          name='word_embeddings')
    else:
      embedding_layer_inst = embedding_layer
    word_embeddings = embedding_layer_inst(word_ids)

    # Roformer does not need a position embedding layer
    type_embedding_layer = layers.on_device_embedding.OnDeviceEmbedding(
        vocab_size=type_vocab_size,
        embedding_width=embedding_width,
        initializer=tf_utils.clone_initializer(initializer),
        use_one_hot=True,
        name='type_embeddings')
    type_embeddings = type_embedding_layer(type_ids)

    # Roformer does not have absolute position embedding
    embeddings = tf_keras.layers.Add()([word_embeddings, type_embeddings])

    embedding_norm_layer = tf_keras.layers.LayerNormalization(
        name='embeddings/layer_norm', axis=-1, epsilon=1e-12, dtype=tf.float32)

    embeddings = embedding_norm_layer(embeddings)
    embeddings = (tf_keras.layers.Dropout(rate=output_dropout)(embeddings))

    # We project the 'embedding' output to 'hidden_size' if it is not already
    # 'hidden_size'.
    if embedding_width != hidden_size:
      embedding_projection = tf_keras.layers.EinsumDense(
          '...x,xy->...y',
          output_shape=hidden_size,
          bias_axes='y',
          kernel_initializer=tf_utils.clone_initializer(initializer),
          name='embedding_projection')
      embeddings = embedding_projection(embeddings)
    else:
      embedding_projection = None

    transformer_layers = []
    data = embeddings
    attention_mask = layers.SelfAttentionMask()(data, mask)
    encoder_outputs = []
    for i in range(num_layers):
      if i == num_layers - 1 and output_range is not None:
        transformer_output_range = output_range
      else:
        transformer_output_range = None
      layer = roformer_encoder_block.RoformerEncoderBlock(
          num_attention_heads=num_attention_heads,
          inner_dim=inner_dim,
          inner_activation=inner_activation,
          q_max_sequence_length=max_sequence_length,
          kv_max_sequence_length=max_sequence_length,
          output_dropout=output_dropout,
          attention_dropout=attention_dropout,
          norm_first=norm_first,
          output_range=transformer_output_range,
          kernel_initializer=tf_utils.clone_initializer(initializer),
          name='roformer/layer_%d' % i)
      transformer_layers.append(layer)
      data = layer([data, attention_mask])
      encoder_outputs.append(data)

    last_encoder_output = encoder_outputs[-1]
    # Applying a tf.slice op (through subscript notation) to a Keras tensor
    # like this will create a SliceOpLambda layer. This is better than a Lambda
    # layer with Python code, because that is fundamentally less portable.
    first_token_tensor = last_encoder_output[:, 0, :]
    pooler_layer = tf_keras.layers.Dense(
        units=hidden_size,
        activation='tanh',
        kernel_initializer=tf_utils.clone_initializer(initializer),
        name='pooler_transform')
    cls_output = pooler_layer(first_token_tensor)

    outputs = dict(
        sequence_output=encoder_outputs[-1],
        pooled_output=cls_output,
        encoder_outputs=encoder_outputs,
    )

    # Once we've created the network using the Functional API, we call
    # super().__init__ as though we were invoking the Functional API Model
    # constructor, resulting in this object having all the properties of a model
    # created using the Functional API. Once super().__init__ is called, we
    # can assign attributes to `self` - note that all `self` assignments are
    # below this line.
    super(RoformerEncoder, self).__init__(
        inputs=[word_ids, mask, type_ids], outputs=outputs, **kwargs)

    config_dict = {
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
    }

    # We are storing the config dict as a namedtuple here to ensure checkpoint
    # compatibility with an earlier version of this model which did not track
    # the config dict attribute. TF does not track immutable attrs which
    # do not contain Trackables, so by creating a config namedtuple instead of
    # a dict we avoid tracking it.
    config_cls = collections.namedtuple('Config', config_dict.keys())
    self._config = config_cls(**config_dict)
    self._pooler_layer = pooler_layer
    self._transformer_layers = transformer_layers
    self._embedding_norm_layer = embedding_norm_layer
    self._embedding_layer = embedding_layer_inst
    # self._position_embedding_layer = position_embedding_layer
    self._position_embedding_layer = None
    self._type_embedding_layer = type_embedding_layer
    if embedding_projection is not None:
      self._embedding_projection = embedding_projection