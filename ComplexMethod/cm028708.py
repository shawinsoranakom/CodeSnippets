def call(self, query, value, key=None, attention_mask=None, cache=None,
           training=False):
    """Compute attention with kernel mechanism.

    Args:
      query: Query `Tensor` of shape `[B, T, dim]`.
      value: Value `Tensor` of shape `[B, S, dim]`.
      key: Optional key `Tensor` of shape `[B, S, dim]`. If not given, will use
        `value` for both `key` and `value`, which is the most common case.
      attention_mask: a boolean mask of shape `[B, S]`, that prevents attenting
        to masked positions. Note that the mask is only appied to the keys. User
        may want to mask the output if query contains pads.
      cache: Cache to accumulate history in memory. Used at inferecne time
        (streaming, decoding) for  causal attention.
      training: Python boolean indicating whether the layer should behave in
        training mode (adding dropout) or in inference mode (doing nothing).

    Returns:
      Multi-headed outputs of attention computation.
    """
    if cache is not None:
      if training:
        raise ValueError(
            "Cache is not supported when training is True.")
      if not self.use_causal_windowed:
        raise ValueError(
            "Cache is not supported for non use_causal_windowed case.")
      if self._begin_kernel:
        raise ValueError(
            "Cache is not supported when begin_kernel is set since the bahvior "
            "is too complicated.")
      if self._feature_transform in _NON_CAUSAL_SUPPORT_TRANSFORM_MAP:
        raise ValueError("Cache is not supported for feature_transform %s" %
                         (self._feature_transform))

    if not self._built_from_signature:
      self._build_from_signature(query=query, value=value, key=key)
    if key is None:
      key = value

    #   N = `num_attention_heads`
    #   H = `size_per_head`
    # `query` = [B, T, N ,H]
    query = self._query_dense(query)

    # `key` = [B, S, N, H]
    key = self._key_dense(key)

    # `value` = [B, S, N, D]
    value = self._value_dense(value)

    if self._begin_kernel > 0:
      attention_output_softmax = self._compute_attention(
          query[:, :self._begin_kernel], key, value, "identity", True,
          attention_mask, training)
      attention_output_softmax = self._dropout_softmax(attention_output_softmax)
      attention_output_softmax = self._output_dense_softmax(
          attention_output_softmax)

      attention_output_kernel = self._compute_attention(
          query[:, self._begin_kernel:], key, value, self._feature_transform,
          self._is_short_seq, attention_mask, training)
      attention_output_kernel = self._dropout_layer(attention_output_kernel)
      attention_output_kernel = self._output_dense(attention_output_kernel)
      attention_output = tf.concat(
          [attention_output_softmax, attention_output_kernel], axis=1)
    else:
      attention_output = self._compute_attention(query, key, value,
                                                 self._feature_transform,
                                                 self._is_short_seq,
                                                 attention_mask,
                                                 cache,
                                                 training)
      # This is actually dropping out entire tokens to attend to, which might
      # seem a bit unusual, but is taken from the original Transformer paper.
      attention_output = self._dropout_layer(attention_output)
      attention_output = self._output_dense(attention_output)
    return attention_output