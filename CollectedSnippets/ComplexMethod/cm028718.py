def __init__(self,
               config: T5TransformerParams,
               shared_embedding: Optional[tf.Variable] = None,
               compute_dtype: tf.DType = tf.float32,
               **kwargs):
    super().__init__(**kwargs)
    self.config = config
    self.compute_dtype = compute_dtype
    if self.config.num_decoder_layers is None:
      self.config.num_decoder_layers = self.config.num_layers
    if not hasattr(
        self.config,
        "target_vocab_size") or self.config.target_vocab_size is None:
      self.config.target_vocab_size = self.config.vocab_size
    with self.name_scope:
      # Target Embedding.
      if shared_embedding is None:
        self.target_embed = Embed(
            vocab_size=self.config.target_vocab_size,
            features=self.config.d_model,
            embeddings_initializer=self.config.vocab_embeddings_initializer,
            dtype=self.dtype,
            compute_dtype=self.compute_dtype,
            name="target_embedding")
      else:
        self.target_embed = shared_embedding
      self.target_dropout = Dropout(self.config.dropout_rate,)
      # Position bias for the target self attention.
      if config.use_shared_relative_position_bias:
        self.relative_embedding = RelativePositionEmbedding(
            num_heads=self.config.num_heads,
            relative_attention_num_buckets=self.config
            .relative_attention_num_buckets,
            relative_attention_max_distance=self.config
            .relative_attention_max_distance,
            bidirectional=self.config.bidirectional,
            embeddings_initializer=self.config.relative_embeddings_initializer,
            dtype=self.dtype,
            compute_dtype=self.compute_dtype,
            name="relative_posemb")
      else:
        self.relative_embeddings = []
        for layer_idx in range(self.config.num_decoder_layers):
          relative_embedding = RelativePositionEmbedding(
              num_heads=self.config.num_heads,
              relative_attention_num_buckets=self.config
              .relative_attention_num_buckets,
              relative_attention_max_distance=self.config
              .relative_attention_max_distance,
              bidirectional=self.config.bidirectional,
              embeddings_initializer=self.config
              .relative_embeddings_initializer,
              dtype=self.dtype,
              compute_dtype=self.compute_dtype,
              name=f"relative_posemb_{layer_idx}")
          self.relative_embeddings.append(relative_embedding)
      self.decoder_layers = []
      for layer_idx in range(self.config.num_decoder_layers):
        if self.config.layer_sharing and layer_idx > 0:
          self.decoder_layers.append(self.decoder_layers[0])
        else:
          self.decoder_layers.append(
              EncDecoderBlock(
                  d_model=self.config.d_model,
                  d_kv=self.config.d_kv,
                  num_heads=self.config.num_heads,
                  d_ff=self.config.d_ff,
                  dropout_rate=self.config.dropout_rate,
                  ffn_activations=self.config.ffn_activations,
                  rescale_query=self.config.rescale_query,
                  weight_initializer=self.config.weight_initializer,
                  bias_initializer=self.config.bias_initializer,
                  dtype=self.dtype,
                  name="decoder_block_%d" % layer_idx))
      self.output_norm = RMSNorm(
          hidden_size=self.config.d_model,
          epsilon=self.config.layer_norm_epsilon,
          dtype=self.dtype,
          name="final_layer_norm")
      self.output_dropout = Dropout(self.config.dropout_rate,)
      if not self.config.logits_via_embedding:
        self.logits_dense = Linear(
            in_features=self.config.d_model,
            out_features=self.config.target_vocab_size,
            use_bias=False,
            dtype=self.dtype,
            name="logits")