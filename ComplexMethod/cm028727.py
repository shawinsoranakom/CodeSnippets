def call(self, inputs):
    """Implements call() for the layer."""
    input_ids = inputs["input_ids"]
    segment_ids = inputs["segment_ids"]
    input_mask = inputs["input_mask"]
    state = inputs["state"]
    permutation_mask = inputs["permutation_mask"]
    target_mapping = inputs["target_mapping"]
    masked_tokens = inputs["masked_tokens"]

    batch_size = tf.shape(input_ids)[0]
    seq_length = tf.shape(input_ids)[1]
    if state is not None:
      memory_length = tf.shape(state[0])[1]
    else:
      memory_length = 0
    total_length = memory_length + seq_length

    if self._two_stream and masked_tokens is None:
      raise ValueError("`masked_tokens` must be provided in order to "
                       "initialize the query stream in "
                       "`TwoStreamRelativeAttention`.")
    if masked_tokens is not None and not self._two_stream:
      logging.warning("`masked_tokens` is provided but `two_stream` is not "
                      "enabled. Please enable `two_stream` to enable two "
                      "stream attention.")

    if input_mask is not None:
      dtype = input_mask.dtype
    elif permutation_mask is not None:
      dtype = permutation_mask.dtype
    else:
      dtype = tf.int32
    query_attention_mask, content_attention_mask = _compute_attention_mask(
        input_mask=input_mask,
        permutation_mask=permutation_mask,
        attention_type=self._attention_type,
        seq_length=seq_length,
        memory_length=memory_length,
        batch_size=batch_size,
        dtype=dtype)
    relative_position_encoding = _compute_positional_encoding(
        attention_type=self._attention_type,
        position_encoding_layer=self.position_encoding,
        hidden_size=self._hidden_size,
        batch_size=batch_size,
        total_length=total_length,
        seq_length=seq_length,
        clamp_length=self._clamp_length,
        bi_data=self._bi_data,
        dtype=tf.float32)
    relative_position_encoding = self.embedding_dropout(
        relative_position_encoding)

    if segment_ids is None:
      segment_embedding = None
      segment_matrix = None
    else:
      if self._segment_embedding is None:
        self._segment_embedding = self.add_weight(
            "seg_embed",
            shape=[self._num_layers, 2, self._num_attention_heads,
                   self._head_size],
            dtype=tf.float32,
            initializer=tf_utils.clone_initializer(self._initializer))

      segment_embedding = self._segment_embedding
      segment_matrix = _compute_segment_matrix(
          segment_ids=segment_ids,
          memory_length=memory_length,
          batch_size=batch_size,
          use_cls_mask=self._use_cls_mask)

    word_embeddings = self._embedding_layer(input_ids)
    content_stream = self._dropout(word_embeddings)

    if self._two_stream:
      if self._mask_embedding is None:
        self._mask_embedding = self.add_weight(
            "mask_emb/mask_emb",
            shape=[1, 1, self._hidden_size],
            dtype=tf.float32)
      if target_mapping is None:
        masked_tokens = masked_tokens[:, :, None]
        masked_token_embedding = (
            masked_tokens * self._mask_embedding +
            (1 - masked_tokens) * word_embeddings)
      else:
        masked_token_embedding = tf.tile(
            self._mask_embedding,
            [batch_size, tf.shape(target_mapping)[1], 1])
      query_stream = self._dropout(masked_token_embedding)
    else:
      query_stream = None

    return self._transformer_xl(
        content_stream=content_stream,
        query_stream=query_stream,
        target_mapping=target_mapping,
        state=state,
        relative_position_encoding=relative_position_encoding,
        segment_matrix=segment_matrix,
        segment_embedding=segment_embedding,
        content_attention_mask=content_attention_mask,
        query_attention_mask=query_attention_mask)