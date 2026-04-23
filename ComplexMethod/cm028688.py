def build_encoder(config: EncoderConfig,
                  embedding_layer: Optional[tf_keras.layers.Layer] = None,
                  encoder_cls=None,
                  bypass_config: bool = False):
  """Instantiate a Transformer encoder network from EncoderConfig.

  Args:
    config: the one-of encoder config, which provides encoder parameters of a
      chosen encoder.
    embedding_layer: an external embedding layer passed to the encoder.
    encoder_cls: an external encoder cls not included in the supported encoders,
      usually used by gin.configurable.
    bypass_config: whether to ignore config instance to create the object with
      `encoder_cls`.

  Returns:
    An encoder instance.
  """
  if bypass_config:
    return encoder_cls()
  encoder_type = config.type
  encoder_cfg = config.get()
  if encoder_cls and encoder_cls.__name__ == "EncoderScaffold":
    embedding_cfg = dict(
        vocab_size=encoder_cfg.vocab_size,
        type_vocab_size=encoder_cfg.type_vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        max_seq_length=encoder_cfg.max_position_embeddings,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        dropout_rate=encoder_cfg.dropout_rate,
    )
    hidden_cfg = dict(
        num_attention_heads=encoder_cfg.num_attention_heads,
        intermediate_size=encoder_cfg.intermediate_size,
        intermediate_activation=tf_utils.get_activation(
            encoder_cfg.hidden_activation),
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
    )
    kwargs = dict(
        embedding_cfg=embedding_cfg,
        hidden_cfg=hidden_cfg,
        num_hidden_instances=encoder_cfg.num_layers,
        pooled_output_dim=encoder_cfg.hidden_size,
        pooler_layer_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        return_all_layer_outputs=encoder_cfg.return_all_encoder_outputs,
        dict_outputs=True)
    return encoder_cls(**kwargs)

  if encoder_type == "any":
    encoder = encoder_cfg.BUILDER(encoder_cfg)
    if not isinstance(encoder,
                      (tf.Module, tf_keras.Model, tf_keras.layers.Layer)):
      raise ValueError("The BUILDER returns an unexpected instance. The "
                       "`build_encoder` should returns a tf.Module, "
                       "tf_keras.Model or tf_keras.layers.Layer. However, "
                       f"we get {encoder.__class__}")
    return encoder

  if encoder_type == "mobilebert":
    return networks.MobileBERTEncoder(
        word_vocab_size=encoder_cfg.word_vocab_size,
        word_embed_size=encoder_cfg.word_embed_size,
        type_vocab_size=encoder_cfg.type_vocab_size,
        max_sequence_length=encoder_cfg.max_sequence_length,
        num_blocks=encoder_cfg.num_blocks,
        hidden_size=encoder_cfg.hidden_size,
        num_attention_heads=encoder_cfg.num_attention_heads,
        intermediate_size=encoder_cfg.intermediate_size,
        intermediate_act_fn=encoder_cfg.hidden_activation,
        hidden_dropout_prob=encoder_cfg.hidden_dropout_prob,
        attention_probs_dropout_prob=encoder_cfg.attention_probs_dropout_prob,
        intra_bottleneck_size=encoder_cfg.intra_bottleneck_size,
        initializer_range=encoder_cfg.initializer_range,
        use_bottleneck_attention=encoder_cfg.use_bottleneck_attention,
        key_query_shared_bottleneck=encoder_cfg.key_query_shared_bottleneck,
        num_feedforward_networks=encoder_cfg.num_feedforward_networks,
        normalization_type=encoder_cfg.normalization_type,
        classifier_activation=encoder_cfg.classifier_activation,
        input_mask_dtype=encoder_cfg.input_mask_dtype)

  if encoder_type == "albert":
    return networks.AlbertEncoder(
        vocab_size=encoder_cfg.vocab_size,
        embedding_width=encoder_cfg.embedding_width,
        hidden_size=encoder_cfg.hidden_size,
        num_layers=encoder_cfg.num_layers,
        num_attention_heads=encoder_cfg.num_attention_heads,
        max_sequence_length=encoder_cfg.max_position_embeddings,
        type_vocab_size=encoder_cfg.type_vocab_size,
        intermediate_size=encoder_cfg.intermediate_size,
        activation=tf_utils.get_activation(encoder_cfg.hidden_activation),
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        dict_outputs=True)

  if encoder_type == "bigbird":
    # TODO(frederickliu): Support use_gradient_checkpointing and update
    # experiments to use the EncoderScaffold only.
    if encoder_cfg.use_gradient_checkpointing:
      return bigbird_encoder.BigBirdEncoder(
          vocab_size=encoder_cfg.vocab_size,
          hidden_size=encoder_cfg.hidden_size,
          num_layers=encoder_cfg.num_layers,
          num_attention_heads=encoder_cfg.num_attention_heads,
          intermediate_size=encoder_cfg.intermediate_size,
          activation=tf_utils.get_activation(encoder_cfg.hidden_activation),
          dropout_rate=encoder_cfg.dropout_rate,
          attention_dropout_rate=encoder_cfg.attention_dropout_rate,
          num_rand_blocks=encoder_cfg.num_rand_blocks,
          block_size=encoder_cfg.block_size,
          max_position_embeddings=encoder_cfg.max_position_embeddings,
          type_vocab_size=encoder_cfg.type_vocab_size,
          initializer=tf_keras.initializers.TruncatedNormal(
              stddev=encoder_cfg.initializer_range),
          embedding_width=encoder_cfg.embedding_width,
          use_gradient_checkpointing=encoder_cfg.use_gradient_checkpointing)
    embedding_cfg = dict(
        vocab_size=encoder_cfg.vocab_size,
        type_vocab_size=encoder_cfg.type_vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        max_seq_length=encoder_cfg.max_position_embeddings,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        dropout_rate=encoder_cfg.dropout_rate)
    attention_cfg = dict(
        num_heads=encoder_cfg.num_attention_heads,
        key_dim=int(encoder_cfg.hidden_size // encoder_cfg.num_attention_heads),
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        max_rand_mask_length=encoder_cfg.max_position_embeddings,
        num_rand_blocks=encoder_cfg.num_rand_blocks,
        from_block_size=encoder_cfg.block_size,
        to_block_size=encoder_cfg.block_size,
        )
    hidden_cfg = dict(
        num_attention_heads=encoder_cfg.num_attention_heads,
        intermediate_size=encoder_cfg.intermediate_size,
        intermediate_activation=tf_utils.get_activation(
            encoder_cfg.hidden_activation),
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        norm_first=encoder_cfg.norm_first,
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        attention_cls=layers.BigBirdAttention,
        attention_cfg=attention_cfg)
    kwargs = dict(
        embedding_cfg=embedding_cfg,
        hidden_cls=layers.TransformerScaffold,
        hidden_cfg=hidden_cfg,
        num_hidden_instances=encoder_cfg.num_layers,
        mask_cls=layers.BigBirdMasks,
        mask_cfg=dict(block_size=encoder_cfg.block_size),
        pooled_output_dim=encoder_cfg.hidden_size,
        pooler_layer_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        return_all_layer_outputs=False,
        dict_outputs=True,
        layer_idx_as_attention_seed=True)
    return networks.EncoderScaffold(**kwargs)

  if encoder_type == "funnel":

    if encoder_cfg.hidden_activation == "gelu":
      activation = tf_utils.get_activation(
          encoder_cfg.hidden_activation,
          approximate=encoder_cfg.approx_gelu)
    else:
      activation = tf_utils.get_activation(encoder_cfg.hidden_activation)

    return networks.FunnelTransformerEncoder(
        vocab_size=encoder_cfg.vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        num_layers=encoder_cfg.num_layers,
        num_attention_heads=encoder_cfg.num_attention_heads,
        max_sequence_length=encoder_cfg.max_position_embeddings,
        type_vocab_size=encoder_cfg.type_vocab_size,
        inner_dim=encoder_cfg.inner_dim,
        inner_activation=activation,
        output_dropout=encoder_cfg.dropout_rate,
        attention_dropout=encoder_cfg.attention_dropout_rate,
        pool_type=encoder_cfg.pool_type,
        pool_stride=encoder_cfg.pool_stride,
        unpool_length=encoder_cfg.unpool_length,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        output_range=encoder_cfg.output_range,
        embedding_width=encoder_cfg.embedding_width,
        embedding_layer=embedding_layer,
        norm_first=encoder_cfg.norm_first,
        share_rezero=encoder_cfg.share_rezero,
        append_dense_inputs=encoder_cfg.append_dense_inputs,
        transformer_cls=encoder_cfg.transformer_cls,
        )

  if encoder_type == "kernel":
    embedding_cfg = dict(
        vocab_size=encoder_cfg.vocab_size,
        type_vocab_size=encoder_cfg.type_vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        max_seq_length=encoder_cfg.max_position_embeddings,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        dropout_rate=encoder_cfg.dropout_rate)
    attention_cfg = dict(
        num_heads=encoder_cfg.num_attention_heads,
        key_dim=int(encoder_cfg.hidden_size // encoder_cfg.num_attention_heads),
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        feature_transform=encoder_cfg.feature_transform,
        num_random_features=encoder_cfg.num_random_features,
        redraw=encoder_cfg.redraw,
        is_short_seq=encoder_cfg.is_short_seq,
        begin_kernel=encoder_cfg.begin_kernel,
        scale=encoder_cfg.scale,
        )
    hidden_cfg = dict(
        num_attention_heads=encoder_cfg.num_attention_heads,
        intermediate_size=encoder_cfg.intermediate_size,
        intermediate_activation=tf_utils.get_activation(
            encoder_cfg.hidden_activation),
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        norm_first=encoder_cfg.norm_first,
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        attention_cls=layers.KernelAttention,
        attention_cfg=attention_cfg)
    kwargs = dict(
        embedding_cfg=embedding_cfg,
        hidden_cls=layers.TransformerScaffold,
        hidden_cfg=hidden_cfg,
        num_hidden_instances=encoder_cfg.num_layers,
        mask_cls=layers.KernelMask,
        pooled_output_dim=encoder_cfg.hidden_size,
        pooler_layer_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        return_all_layer_outputs=False,
        dict_outputs=True,
        layer_idx_as_attention_seed=True)
    return networks.EncoderScaffold(**kwargs)

  if encoder_type == "xlnet":
    return networks.XLNetBase(
        vocab_size=encoder_cfg.vocab_size,
        num_layers=encoder_cfg.num_layers,
        hidden_size=encoder_cfg.hidden_size,
        num_attention_heads=encoder_cfg.num_attention_heads,
        head_size=encoder_cfg.head_size,
        inner_size=encoder_cfg.inner_size,
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        attention_type=encoder_cfg.attention_type,
        bi_data=encoder_cfg.bi_data,
        two_stream=encoder_cfg.two_stream,
        tie_attention_biases=encoder_cfg.tie_attention_biases,
        memory_length=encoder_cfg.memory_length,
        clamp_length=encoder_cfg.clamp_length,
        reuse_length=encoder_cfg.reuse_length,
        inner_activation=encoder_cfg.inner_activation,
        use_cls_mask=encoder_cfg.use_cls_mask,
        embedding_width=encoder_cfg.embedding_width,
        initializer=tf_keras.initializers.RandomNormal(
            stddev=encoder_cfg.initializer_range))

  if encoder_type == "reuse":
    embedding_cfg = dict(
        vocab_size=encoder_cfg.vocab_size,
        type_vocab_size=encoder_cfg.type_vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        max_seq_length=encoder_cfg.max_position_embeddings,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        dropout_rate=encoder_cfg.dropout_rate)
    hidden_cfg = dict(
        num_attention_heads=encoder_cfg.num_attention_heads,
        inner_dim=encoder_cfg.intermediate_size,
        inner_activation=tf_utils.get_activation(
            encoder_cfg.hidden_activation),
        output_dropout=encoder_cfg.dropout_rate,
        attention_dropout=encoder_cfg.attention_dropout_rate,
        norm_first=encoder_cfg.norm_first,
        kernel_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        reuse_attention=encoder_cfg.reuse_attention,
        use_relative_pe=encoder_cfg.use_relative_pe,
        pe_max_seq_length=encoder_cfg.pe_max_seq_length,
        max_reuse_layer_idx=encoder_cfg.max_reuse_layer_idx)
    kwargs = dict(
        embedding_cfg=embedding_cfg,
        hidden_cls=layers.ReuseTransformer,
        hidden_cfg=hidden_cfg,
        num_hidden_instances=encoder_cfg.num_layers,
        pooled_output_dim=encoder_cfg.hidden_size,
        pooler_layer_initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        return_all_layer_outputs=False,
        dict_outputs=True,
        feed_layer_idx=True,
        recursive=True)
    return networks.EncoderScaffold(**kwargs)

  if encoder_type == "query_bert":
    embedding_layer = layers.FactorizedEmbedding(
        vocab_size=encoder_cfg.vocab_size,
        embedding_width=encoder_cfg.embedding_size,
        output_dim=encoder_cfg.hidden_size,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        name="word_embeddings")
    return networks.BertEncoderV2(
        vocab_size=encoder_cfg.vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        num_layers=encoder_cfg.num_layers,
        num_attention_heads=encoder_cfg.num_attention_heads,
        intermediate_size=encoder_cfg.intermediate_size,
        activation=tf_utils.get_activation(encoder_cfg.hidden_activation),
        dropout_rate=encoder_cfg.dropout_rate,
        attention_dropout_rate=encoder_cfg.attention_dropout_rate,
        max_sequence_length=encoder_cfg.max_position_embeddings,
        type_vocab_size=encoder_cfg.type_vocab_size,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        output_range=encoder_cfg.output_range,
        embedding_layer=embedding_layer,
        return_all_encoder_outputs=encoder_cfg.return_all_encoder_outputs,
        return_attention_scores=encoder_cfg.return_attention_scores,
        dict_outputs=True,
        norm_first=encoder_cfg.norm_first)

  if encoder_type == "fnet":
    return networks.FNet(
        vocab_size=encoder_cfg.vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        num_layers=encoder_cfg.num_layers,
        num_attention_heads=encoder_cfg.num_attention_heads,
        inner_dim=encoder_cfg.inner_dim,
        inner_activation=tf_utils.get_activation(encoder_cfg.inner_activation),
        output_dropout=encoder_cfg.output_dropout,
        attention_dropout=encoder_cfg.attention_dropout,
        max_sequence_length=encoder_cfg.max_sequence_length,
        type_vocab_size=encoder_cfg.type_vocab_size,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        output_range=encoder_cfg.output_range,
        embedding_width=encoder_cfg.embedding_width,
        embedding_layer=embedding_layer,
        norm_first=encoder_cfg.norm_first,
        use_fft=encoder_cfg.use_fft,
        attention_layers=encoder_cfg.attention_layers)

  if encoder_type == "sparse_mixer":
    return networks.SparseMixer(
        vocab_size=encoder_cfg.vocab_size,
        hidden_size=encoder_cfg.hidden_size,
        num_layers=encoder_cfg.num_layers,
        moe_layers=encoder_cfg.moe_layers,
        attention_layers=encoder_cfg.attention_layers,
        num_experts=encoder_cfg.num_experts,
        train_capacity_factor=encoder_cfg.train_capacity_factor,
        eval_capacity_factor=encoder_cfg.eval_capacity_factor,
        examples_per_group=encoder_cfg.examples_per_group,
        use_fft=encoder_cfg.use_fft,
        num_attention_heads=encoder_cfg.num_attention_heads,
        max_sequence_length=encoder_cfg.max_sequence_length,
        type_vocab_size=encoder_cfg.type_vocab_size,
        inner_dim=encoder_cfg.inner_dim,
        inner_activation=tf_utils.get_activation(encoder_cfg.inner_activation),
        output_dropout=encoder_cfg.output_dropout,
        attention_dropout=encoder_cfg.attention_dropout,
        initializer=tf_keras.initializers.TruncatedNormal(
            stddev=encoder_cfg.initializer_range),
        output_range=encoder_cfg.output_range,
        embedding_width=encoder_cfg.embedding_width,
        norm_first=encoder_cfg.norm_first,
        embedding_layer=embedding_layer)

  bert_encoder_cls = networks.BertEncoder
  if encoder_type == "bert_v2":
    bert_encoder_cls = networks.BertEncoderV2

  # Uses the default BERTEncoder configuration schema to create the encoder.
  # If it does not match, please add a switch branch by the encoder type.
  return bert_encoder_cls(
      vocab_size=encoder_cfg.vocab_size,
      hidden_size=encoder_cfg.hidden_size,
      num_layers=encoder_cfg.num_layers,
      num_attention_heads=encoder_cfg.num_attention_heads,
      intermediate_size=encoder_cfg.intermediate_size,
      activation=tf_utils.get_activation(encoder_cfg.hidden_activation),
      dropout_rate=encoder_cfg.dropout_rate,
      attention_dropout_rate=encoder_cfg.attention_dropout_rate,
      max_sequence_length=encoder_cfg.max_position_embeddings,
      type_vocab_size=encoder_cfg.type_vocab_size,
      initializer=tf_keras.initializers.TruncatedNormal(
          stddev=encoder_cfg.initializer_range),
      output_range=encoder_cfg.output_range,
      embedding_width=encoder_cfg.embedding_size,
      embedding_layer=embedding_layer,
      return_all_encoder_outputs=encoder_cfg.return_all_encoder_outputs,
      return_attention_scores=encoder_cfg.return_attention_scores,
      return_word_embeddings=encoder_cfg.return_word_embeddings,
      dict_outputs=True,
      norm_first=encoder_cfg.norm_first)