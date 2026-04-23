def call(self,
           query,
           value,
           key=None,
           attention_mask=None,
           return_attention_scores=False,
           training=None,
           reuse_attention_scores=None):
    if self._reuse_heads > 0 and reuse_attention_scores is None:
      raise ValueError("reuse_attention_scores cannot be None when "
                       "reuse_attention is True or > 0.")
    if not self._built_from_signature:
      self._build_from_signature(query=query, value=value, key=key)
    if key is None:
      key = value

    #   N = `num_attention_heads`
    #   H = `size_per_head`
    # `value` = [B, S, N, H]
    value = [vd(value) for vd in self._value_dense]
    if self._reuse_heads < self._num_heads:
      # `query` = [B, T, N ,H]
      query = self._query_dense(query)

      # `key` = [B, S, N, H]
      key = self._key_dense(key)
    else:
      query, key = None, None

    attention_output, attention_scores = self._compute_attention(
        query, key, value, reuse_attention_scores, attention_mask, training)
    attention_output = [od(attention_output[i]) for i, od in enumerate(
        self._output_dense)]
    if len(attention_output) == 1:
      attention_output = attention_output[0]
    else:
      attention_output = attention_output[0] + attention_output[1]

    if return_attention_scores:
      return attention_output, attention_scores
    return attention_output