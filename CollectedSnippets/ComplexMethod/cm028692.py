def _compute_attention(
      self, query, key, value, attention_mask=None, training=None
  ):
    # If block sizes are same as sequence lengths, we defer to default attn.
    if (
        self._query_shape[-2] == self._src_block_size
        and self._key_shape[-2] == self._tgt_block_size
    ):
      logging.info(
          "Computing default attention as block sizes are equal to sequence"
          " lengths."
      )
      # pytype: disable=attribute-error
      return super()._compute_attention(
          query,
          key,
          value,
          attention_mask=attention_mask,
          training=training,
      )
      # pytype: enable=attribute-error
    # src_num_blocks and tgt_num_blocks are the number of blocks in the source
    # and target. Care should be taken to ensure that the number of blocks in
    # the source and target are the same.
    if self._query_shape[-2] % self._src_block_size != 0:
      raise ValueError(
          "query_shape[-2] must be divisible by src_block_size."
      )
    if self._key_shape[-2] % self._tgt_block_size != 0:
      raise ValueError(
          "key_shape[-2] must be divisible by tgt_block_size."
      )
    src_num_blocks = self._query_shape[-2] // self._src_block_size
    tgt_num_blocks = self._key_shape[-2] // self._tgt_block_size

    if src_num_blocks != tgt_num_blocks and tgt_num_blocks != 1:
      raise ValueError(
          "src_num_blocks must be equal to tgt_num_blocks."
      )
    # Convert the query/key/value into blocks to perform block diagonal
    # attention.
    query_blocks = tf.reshape(query, [
        -1,
        self._num_heads,
        src_num_blocks,
        self._src_block_size,
        self._key_dim,
    ])
    if tgt_num_blocks != 1 and self._num_kv_heads != 1:
      key_blocks = tf.reshape(key, [
          -1,
          self._num_heads,
          tgt_num_blocks,
          self._tgt_block_size,
          self._key_dim,
      ])
      value_blocks = tf.reshape(value, [
          -1,
          self._num_heads,
          tgt_num_blocks,
          self._tgt_block_size,
          self._value_dim,
      ])
    elif tgt_num_blocks != 1 and self._num_kv_heads == 1:
      key_blocks = tf.reshape(key, [
          -1,
          tgt_num_blocks,
          self._tgt_block_size,
          self._key_dim,
      ])
      value_blocks = tf.reshape(value, [
          -1,
          tgt_num_blocks,
          self._tgt_block_size,
          self._value_dim,
      ])
    else:
      key_blocks = key
      value_blocks = value
    if attention_mask is not None:
      attention_mask = self._block_diagonal_mask(attention_mask, key.dtype)
    # pytype: disable=attribute-error
    attention_output, attention_scores = super()._compute_attention(
        query_blocks,
        key_blocks,
        value_blocks,
        attention_mask=attention_mask,
        training=training,
    )
    # pytype: enable=attribute-error
    # Reshape the attention output to the original shape.
    attention_output = tf.reshape(attention_output, [
        -1,
        self._num_heads,
        self._query_shape[1],
        self._value_dim,
    ])
    return attention_output, attention_scores