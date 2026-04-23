def __init__(
      self,
      mlp_dim=3072,
      num_heads=12,
      num_layers=12,
      attention_dropout_rate=0.0,
      dropout_rate=0.1,
      init_stochastic_depth_rate=0.0,
      input_specs=layers.InputSpec(shape=[None, None, None, 3]),
      patch_size=16,
      hidden_size=768,
      representation_size=0,
      pooler='token',
      kernel_regularizer=None,
      original_init: bool = True,
      output_encoded_tokens: bool = True,
      output_2d_feature_maps: bool = False,
      pos_embed_shape: Optional[Tuple[int, int]] = None,
      layer_scale_init_value: float = 0.0,
      transformer_partition_dims: Optional[Tuple[int, int, int, int]] = None,
      output_attention_scores: bool = False,
  ):
    """VisionTransformer initialization function."""
    self._mlp_dim = mlp_dim
    self._num_heads = num_heads
    self._num_layers = num_layers
    self._hidden_size = hidden_size
    self._patch_size = patch_size

    inputs = tf_keras.Input(shape=input_specs.shape[1:])

    x = layers.Conv2D(
        filters=hidden_size,
        kernel_size=patch_size,
        strides=patch_size,
        padding='valid',
        kernel_regularizer=kernel_regularizer,
        kernel_initializer='lecun_normal' if original_init else 'he_uniform')(
            inputs)
    if tf_keras.backend.image_data_format() == 'channels_last':
      rows_axis, cols_axis = (1, 2)
    else:
      rows_axis, cols_axis = (2, 3)
      # The reshape below assumes the data_format is 'channels_last,' so
      # transpose to that. Once the data is flattened by the reshape, the
      # data_format is irrelevant, so no need to update
      # tf_keras.backend.image_data_format.
      x = tf.transpose(x, perm=[0, 2, 3, 1])

    pos_embed_target_shape = (x.shape[rows_axis], x.shape[cols_axis])
    feat_h = input_specs.shape[rows_axis] // patch_size
    feat_w = input_specs.shape[cols_axis] // patch_size
    seq_len = feat_h * feat_w
    x = tf.reshape(x, [-1, seq_len, hidden_size])

    # If we want to add a class token, add it here.
    if pooler == 'token':
      x = TokenLayer(name='cls')(x)

    encoder_output = Encoder(
        num_layers=num_layers,
        mlp_dim=mlp_dim,
        num_heads=num_heads,
        dropout_rate=dropout_rate,
        attention_dropout_rate=attention_dropout_rate,
        kernel_regularizer=kernel_regularizer,
        kernel_initializer='glorot_uniform'
        if original_init
        else dict(class_name='TruncatedNormal', config=dict(stddev=0.02)),
        init_stochastic_depth_rate=init_stochastic_depth_rate,
        pos_embed_origin_shape=pos_embed_shape,
        pos_embed_target_shape=pos_embed_target_shape,
        layer_scale_init_value=layer_scale_init_value,
        output_attention_scores=output_attention_scores,
    )(x)

    endpoints = {}
    if output_attention_scores:
      x, attention_scores = encoder_output
      endpoints['attention_scores'] = attention_scores
    else:
      x = encoder_output

    if pooler == 'token':
      output_feature = x[:, 1:]
      x = x[:, 0]
    elif pooler == 'gap':
      output_feature = x
      x = tf.reduce_mean(x, axis=1)
    elif pooler == 'none':
      output_feature = x
      x = tf.identity(x, name='encoded_tokens')
    else:
      raise ValueError(f'unrecognized pooler type: {pooler}')

    if output_2d_feature_maps:
      # Use the closest feature level.
      feat_level = round(math.log2(patch_size))
      logging.info(
          'VisionTransformer patch size %d and feature level: %d',
          patch_size,
          feat_level,
      )
      endpoints[str(feat_level)] = tf.reshape(
          output_feature, [-1, feat_h, feat_w, x.shape.as_list()[-1]])

      # Don"t include `pre_logits` or `encoded_tokens` to support decoders.
      self._output_specs = {k: v.shape for k, v in endpoints.items()}

    if representation_size:
      x = layers.Dense(
          representation_size,
          kernel_regularizer=kernel_regularizer,
          name='pre_logits',
          kernel_initializer='lecun_normal' if original_init else 'he_uniform',
      )(x)
      x = tf.nn.tanh(x)
    else:
      x = tf.identity(x, name='pre_logits')

    if pooler == 'none':
      if output_encoded_tokens:
        endpoints['encoded_tokens'] = x
    else:
      endpoints['pre_logits'] = tf.reshape(
          x, [-1, 1, 1, representation_size or hidden_size])

    super().__init__(inputs=inputs, outputs=endpoints)