def __init__(self,
               pooled_output_dim,
               pooler_layer_initializer=tf_keras.initializers.TruncatedNormal(
                   stddev=0.02),
               embedding_cls=None,
               embedding_cfg=None,
               embedding_data=None,
               num_hidden_instances=1,
               hidden_cls=layers.Transformer,
               hidden_cfg=None,
               mask_cls=layers.SelfAttentionMask,
               mask_cfg=None,
               layer_norm_before_pooling=False,
               return_all_layer_outputs=False,
               dict_outputs=False,
               layer_idx_as_attention_seed=False,
               feed_layer_idx=False,
               recursive=False,
               **kwargs):

    if embedding_cls:
      if inspect.isclass(embedding_cls):
        embedding_network = embedding_cls(
            **embedding_cfg) if embedding_cfg else embedding_cls()
      else:
        embedding_network = embedding_cls
      inputs = embedding_network.inputs
      embeddings, attention_mask = embedding_network(inputs)
      embedding_layer = None
      position_embedding_layer = None
      type_embedding_layer = None
      embedding_norm_layer = None
    else:
      embedding_network = None
      seq_length = embedding_cfg.get('seq_length', None)
      word_ids = tf_keras.layers.Input(
          shape=(seq_length,), dtype=tf.int32, name='input_word_ids')
      mask = tf_keras.layers.Input(
          shape=(seq_length,), dtype=tf.int32, name='input_mask')
      type_ids = tf_keras.layers.Input(
          shape=(seq_length,), dtype=tf.int32, name='input_type_ids')
      inputs = [word_ids, mask, type_ids]

      embedding_layer = layers.OnDeviceEmbedding(
          vocab_size=embedding_cfg['vocab_size'],
          embedding_width=embedding_cfg['hidden_size'],
          initializer=tf_utils.clone_initializer(embedding_cfg['initializer']),
          name='word_embeddings')

      word_embeddings = embedding_layer(word_ids)

      # Always uses dynamic slicing for simplicity.
      position_embedding_layer = layers.PositionEmbedding(
          initializer=tf_utils.clone_initializer(embedding_cfg['initializer']),
          max_length=embedding_cfg['max_seq_length'],
          name='position_embedding')
      position_embeddings = position_embedding_layer(word_embeddings)

      type_embedding_layer = layers.OnDeviceEmbedding(
          vocab_size=embedding_cfg['type_vocab_size'],
          embedding_width=embedding_cfg['hidden_size'],
          initializer=tf_utils.clone_initializer(embedding_cfg['initializer']),
          use_one_hot=True,
          name='type_embeddings')
      type_embeddings = type_embedding_layer(type_ids)

      embeddings = tf_keras.layers.Add()(
          [word_embeddings, position_embeddings, type_embeddings])

      embedding_norm_layer = tf_keras.layers.LayerNormalization(
          name='embeddings/layer_norm',
          axis=-1,
          epsilon=1e-12,
          dtype=tf.float32)
      embeddings = embedding_norm_layer(embeddings)

      embeddings = (
          tf_keras.layers.Dropout(
              rate=embedding_cfg['dropout_rate'])(embeddings))

      mask_cfg = {} if mask_cfg is None else mask_cfg
      if inspect.isclass(mask_cls):
        mask_layer = mask_cls(**mask_cfg)
      else:
        mask_layer = mask_cls
      attention_mask = mask_layer(embeddings, mask)

    data = embeddings

    layer_output_data = []
    hidden_layers = []
    hidden_cfg = hidden_cfg if hidden_cfg else {}

    if isinstance(hidden_cls, list) and len(hidden_cls) != num_hidden_instances:
      raise RuntimeError(
          ('When input hidden_cls to EncoderScaffold %s is a list, it must '
           'contain classes or instances with size specified by '
           'num_hidden_instances, got %d vs %d.') % self.name, len(hidden_cls),
          num_hidden_instances)
    # Consider supporting customized init states.
    recursive_states = None
    for i in range(num_hidden_instances):
      if isinstance(hidden_cls, list):
        cur_hidden_cls = hidden_cls[i]
      else:
        cur_hidden_cls = hidden_cls
      if inspect.isclass(cur_hidden_cls):
        if hidden_cfg and 'attention_cfg' in hidden_cfg and (
            layer_idx_as_attention_seed):
          hidden_cfg = copy.deepcopy(hidden_cfg)
          hidden_cfg['attention_cfg']['seed'] = i
        if feed_layer_idx:
          hidden_cfg['layer_idx'] = i
        layer = cur_hidden_cls(**hidden_cfg)
      else:
        layer = cur_hidden_cls
      if recursive:
        data, recursive_states = layer([data, attention_mask, recursive_states])
      else:
        data = layer([data, attention_mask])
      layer_output_data.append(data)
      hidden_layers.append(layer)

    if layer_norm_before_pooling:
      # Normalize the final output.
      output_layer_norm = tf_keras.layers.LayerNormalization(
          name='final_layer_norm',
          axis=-1,
          epsilon=1e-12)
      layer_output_data[-1] = output_layer_norm(layer_output_data[-1])

    last_layer_output = layer_output_data[-1]
    # Applying a tf.slice op (through subscript notation) to a Keras tensor
    # like this will create a SliceOpLambda layer. This is better than a Lambda
    # layer with Python code, because that is fundamentally less portable.
    first_token_tensor = last_layer_output[:, 0, :]
    pooler_layer_initializer = tf_keras.initializers.get(
        pooler_layer_initializer)
    pooler_layer = tf_keras.layers.Dense(
        units=pooled_output_dim,
        activation='tanh',
        kernel_initializer=pooler_layer_initializer,
        name='cls_transform')
    cls_output = pooler_layer(first_token_tensor)

    if dict_outputs:
      outputs = dict(
          sequence_output=layer_output_data[-1],
          pooled_output=cls_output,
          encoder_outputs=layer_output_data,
      )
    elif return_all_layer_outputs:
      outputs = [layer_output_data, cls_output]
    else:
      outputs = [layer_output_data[-1], cls_output]

    # b/164516224
    # Once we've created the network using the Functional API, we call
    # super().__init__ as though we were invoking the Functional API Model
    # constructor, resulting in this object having all the properties of a model
    # created using the Functional API. Once super().__init__ is called, we
    # can assign attributes to `self` - note that all `self` assignments are
    # below this line.
    super().__init__(
        inputs=inputs, outputs=outputs, **kwargs)

    self._hidden_cls = hidden_cls
    self._hidden_cfg = hidden_cfg
    self._mask_cls = mask_cls
    self._mask_cfg = mask_cfg
    self._num_hidden_instances = num_hidden_instances
    self._pooled_output_dim = pooled_output_dim
    self._pooler_layer_initializer = pooler_layer_initializer
    self._embedding_cls = embedding_cls
    self._embedding_cfg = embedding_cfg
    self._embedding_data = embedding_data
    self._layer_norm_before_pooling = layer_norm_before_pooling
    self._return_all_layer_outputs = return_all_layer_outputs
    self._dict_outputs = dict_outputs
    self._kwargs = kwargs

    self._embedding_layer = embedding_layer
    self._embedding_network = embedding_network
    self._position_embedding_layer = position_embedding_layer
    self._type_embedding_layer = type_embedding_layer
    self._embedding_norm_layer = embedding_norm_layer
    self._hidden_layers = hidden_layers
    if self._layer_norm_before_pooling:
      self._output_layer_norm = output_layer_norm
    self._pooler_layer = pooler_layer
    self._layer_idx_as_attention_seed = layer_idx_as_attention_seed

    logging.info('EncoderScaffold configs: %s', self.get_config())