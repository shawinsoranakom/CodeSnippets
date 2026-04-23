def _compute_attention(self,
                         query,
                         key,
                         value,
                         feature_transform,
                         is_short_seq,
                         attention_mask=None,
                         cache=None,
                         training=False,
                         numeric_stabler=_NUMERIC_STABLER):
    """Applies kernel attention with query, key, value tensors.

    This function defines the computation inside `call` with projected
    multi-head Q, K, V inputs. Users can override this function for customized
    attention implementation.

    Args:
      query: Projected query `Tensor` of shape `[B, T, N, key_dim]`.
      key: Projected key `Tensor` of shape `[B, S, N, key_dim]`.
      value: Projected value `Tensor` of shape `[B, S, N, value_dim]`.
      feature_transform: A non-linear transform of the keys and quries.
      is_short_seq: boolean predicate indicating whether input data consists of
        short or long sequences; usually short sequence is defined as having
        length L <= 1024.
      attention_mask: a boolean mask of shape `[B, S]`, that prevents attenting
        to masked positions. Note that the mask is only appied to the keys. User
        may want to mask the output if query contains pads.
      cache: Cache to accumulate history in memory. Used at inferecne time
        (streaming, decoding) for  causal attention.
      training: Python boolean indicating whether the layer should behave in
        training mode (adding dropout) or in inference mode (doing nothing).
      numeric_stabler: A scalar value added to avoid divide by 0.

    Returns:
      attention_output: Multi-headed outputs of attention computation.
    """
    projection_matrix = None

    if self._num_random_features > 0:
      if self._redraw and training:
        projection_matrix = create_projection_matrix(self._num_random_features,
                                                     self._key_dim)
      else:
        projection_matrix = self._projection_matrix

    if self._scale_by_length:
      scale = tf.math.log(tf.reduce_sum(attention_mask,
                                        axis=-1)) * self._scale / math.log(512)
      scale = tf.reshape(scale, [-1, 1, 1, 1])
    else:
      scale = self._scale
    if is_short_seq:
      # Note: Applying scalar multiply at the smaller end of einsum improves
      # XLA performance, but may introduce slight numeric differences in
      # the Transformer attention head.
      query = query * scale
    else:
      # Note: we suspect spliting the scale to key, query yields smaller
      # approximation variance when random projection is used.
      # For simplicity, we also split when there's no random projection.
      key *= tf.math.sqrt(scale)
      query *= tf.math.sqrt(scale)

    key_prime = _TRANSFORM_MAP[feature_transform](key, query, False,
                                                  projection_matrix)
    query_prime = _TRANSFORM_MAP[feature_transform](query, key, True,
                                                    projection_matrix)

    if attention_mask is not None:
      key_prime = tf.einsum("BSNH,BS->BSNH", key_prime, attention_mask)

    if is_short_seq:
      attention_scores = tf.einsum("BTNH,BSNH->BTSN", query_prime, key_prime)
      attention_scores = tf.nn.softmax(attention_scores, axis=2)
      attention_output = tf.einsum("BTSN,BSNH->BTNH", attention_scores, value)
    elif self.use_causal_windowed:
      attention_output = causal_windowed_performer_attention(
          query_prime,
          key_prime,
          value,
          chunk_length=self.causal_chunk_length,
          window_length=self.causal_window_length,
          window_decay=self.causal_window_decay,
          padding=self.causal_padding,
          cache=cache)
    else:
      kv = tf.einsum("BSNH,BSND->BNDH", key_prime, value)
      denominator = 1.0 / (
          tf.einsum("BTNH,BNH->BTN", query_prime,
                    tf.reduce_sum(key_prime, axis=1)) + _NUMERIC_STABLER)
      attention_output = tf.einsum("BTNH,BNDH,BTN->BTND", query_prime, kv,
                                   denominator)
    return attention_output