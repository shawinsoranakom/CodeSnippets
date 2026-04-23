def __call__(self,
               query,
               mask=None,
               kv=None,
               position_bias=None,
               cache: Optional[Dict[str, tf.Tensor]] = None,
               decode_position=None,
               training=False):
    """MultiHeadAttention at work.

    Args:
      query: Tensor of shape (bs, qlen, d_model).
      mask: None or Tensor of shape (bs, n_heads, qlen, klen).
      kv: None or Tensor of shape (bs, klen, d_model).
      position_bias: None or Tensor of shape (bs, n_heads, qlen, klen).
      cache: If not None, cache["key"] and cache["value"] are Tensors of shape
        (bs, klen, n_heads, d_kv).
      decode_position: If not None, which position of the sequence we are
        decoding for. Ranges from 0 to klen - 1.
      training: Effects the behavior of dropout.

    Returns:
      A dictionary, output["context"] is the output after attention,
        output["cache"] contains updated cache for the next round of
        autoregressive decoding.
    """
    # Input is (bs, qlen, d_model)
    use_cache = cache is not None
    if kv is None:
      kv = query
    q = self.q(query)
    if self.rescale_query:
      q /= tf.math.sqrt(tf.cast(self.d_kv, dtype=q.dtype))
    k = self.k(kv)
    v = self.v(kv)
    if use_cache:
      k, v = self._update_cache(k, v, cache, decode_position)

    # NOTE: T5 does not explicitly rescale the attention logits by
    #       1/sqrt(q_dim)!  This is folded into the initializers of the
    #       linear transformations, which is equivalent under Adafactor.
    scores = tf.einsum("bqnd,bknd->bnqk", q, k)  # (bs, n_heads, qlen, klen)
    if position_bias is not None:
      # If position_bias is None, the input embedings should already include
      # position embeddings.
      if use_cache:
        bias_shape = position_bias.shape.as_list()
        position_bias = tf.slice(
            position_bias, [0, 0, decode_position, 0],
            [bias_shape[0], bias_shape[1], 1, bias_shape[3]])
      scores += position_bias

    if mask is not None:
      scores += mask  # (bs, n_heads, qlen, klen)
    weights = tf.nn.softmax(tf.cast(scores, tf.float32), axis=-1)
    output_scores = weights
    # weights shape = (bs, n_heads, qlen, klen)
    weights = tf.cast(weights, scores.dtype)
    weight_shape = tf_utils.get_shape_list(weights)
    # NOTE: T5 broadcasts along the "length" dim, but unclear which one that
    # corresponds to. We assume it is the query dimension.
    # (bs, n_heads, qlen, klen)
    weight_shape[-2] = 1
    weights = self.dropout(weights, training=training, noise_shape=weight_shape)

    c = tf.einsum("bnqk,bknd->bqnd", weights, v)
    c = self.o(c)

    outputs = dict(context=c)
    outputs["attention_scores"] = output_scores
    if cache:
      outputs["cache"] = cache
    return outputs