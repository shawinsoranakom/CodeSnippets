def call(self,
           hidden_states,
           attention_mask=None,
           is_index_masked=None,
           is_index_global_attn=None,
           training=None):
    """Applies Dot-product attention with query, key, value tensors.

    This function defines the computation inside `call` with projected
    multi-head Q, K, V inputs. Users can override this function for customized
    attention implementation.
    Args:
      hidden_states: inputs for generating query, key and value tensors.
      attention_mask: a boolean mask of shape `(B, T, S)`, that prevents
        attention to certain positions.
      is_index_masked: boolean indicating whether the index is masked.
      is_index_global_attn: boolean indicating whether the index is global
        attention.
      training: Python boolean indicating whether the layer should behave in
        training mode (adding dropout) or in inference mode (doing nothing).

    Returns:
      attention_output: Multi-headed outputs of attention computation.
    """
    if not self._built_from_signature:
      self._build_from_signature(
          query=hidden_states, value=hidden_states, key=hidden_states)

    #   N = `num_attention_heads`
    #   H = `size_per_head`
    # `query` = [B, T, N ,H]
    query = self._query_dense(hidden_states)

    # `key` = [B, S, N, H]
    key = self._key_dense(hidden_states)

    # `value` = [B, S, N, H]
    value = self._value_dense(hidden_states)

    # Note: Applying scalar multiply at the smaller end of einsum improves
    # XLA performance, but may introduce slight numeric differences in
    # the Transformer attention head.
    query = tf.multiply(query, 1.0 / math.sqrt(float(self._key_dim)))
    batch_size, seq_len, num_heads, head_dim = get_shape_list(query)

    # attn_probs = (batch_size, seq_len, num_heads, window*2+1)
    attn_scores = self._sliding_chunks_query_key_matmul(
        query, key, self._one_sided_attn_window_size)

    # diagonal mask with zeros everywhere and -inf inplace of padding
    diagonal_mask = self._sliding_chunks_query_key_matmul(
        tf.ones(get_shape_list(attention_mask)),
        attention_mask,
        self._one_sided_attn_window_size,
    )

    # pad local attention probs
    attn_scores += diagonal_mask

    if tf.executing_eagerly():
      tf.debugging.assert_equal(
          get_shape_list(attn_scores),
          [
              batch_size, seq_len, self._num_heads,
              self._one_sided_attn_window_size * 2 + 1
          ],
          message=f"attn_probs should be of size "
          f"({batch_size}, {seq_len}, {num_heads}, "
          f"{self._one_sided_attn_window_size * 2 + 1}),"
          f" but is of size {get_shape_list(attn_scores)}",
      )

    # compute global attn indices required through out forward fn
    (
        max_num_global_attn_indices,
        is_index_global_attn_nonzero,
        is_local_index_global_attn_nonzero,
        is_local_index_no_global_attn_nonzero,
    ) = self._get_global_attn_indices(is_index_global_attn,
                                      self.global_attention_size)
    # this function is only relevant for global attention
    if self.global_attention_size > 0:
      attn_scores = self._concat_with_global_key_attn_probs(
          attn_scores=attn_scores,
          query_vectors=query,
          key_vectors=key,
          max_num_global_attn_indices=max_num_global_attn_indices,
          is_index_global_attn_nonzero=is_index_global_attn_nonzero,
          is_local_index_global_attn_nonzero=is_local_index_global_attn_nonzero,
          is_local_index_no_global_attn_nonzero=is_local_index_no_global_attn_nonzero,
      )
    else:
      pass

    attn_probs = tf.nn.softmax(attn_scores, axis=-1)

    # softmax sometimes inserts NaN if all positions are masked,
    # replace them with 0
    # Make sure to create a mask with the proper shape:
    # if is_global_attn==True => [batch_size, seq_len, self.num_heads,
    # self.one_sided_attn_window_size * 2 + max_num_global_attn_indices + 1]
    # if is_global_attn==False => [batch_size, seq_len, self.num_heads,
    # self.one_sided_attn_window_size * 2 + 1]
    if self.global_attention_size > 0:
      masked_index = tf.tile(
          is_index_masked[:, :, None, None],
          (1, 1, self._num_heads, self._one_sided_attn_window_size * 2 +
           max_num_global_attn_indices + 1),
      )
    else:
      masked_index = tf.tile(
          is_index_masked[:, :, None, None],
          (1, 1, self._num_heads, self._one_sided_attn_window_size * 2 + 1),
      )

    attn_probs = tf.where(
        masked_index,
        tf.zeros(get_shape_list(masked_index), dtype=attn_probs.dtype),
        attn_probs,
    )

    layer_head_mask = None
    if layer_head_mask is not None:
      if tf.executing_eagerly():
        tf.debugging.assert_equal(
            get_shape_list(layer_head_mask),
            [self._num_heads],
            message=f"Head mask for a single layer should be of size "
            f"{(self._num_heads)}, but is "
            f"{get_shape_list(layer_head_mask)}",
        )

      attn_probs = tf.reshape(layer_head_mask, (1, 1, -1, 1)) * attn_probs

    # apply dropout
    attn_probs = self._dropout_layer(attn_probs, training=training)
    value_vectors = tf.reshape(
        value, (batch_size, seq_len, self._num_heads, self._key_dim))

    # if global attention, compute sum of global and local attn
    if self.global_attention_size > 0:
      attn_output = self._compute_attn_output_with_global_indices(
          value_vectors=value_vectors,
          attn_probs=attn_probs,
          max_num_global_attn_indices=max_num_global_attn_indices,
          is_index_global_attn_nonzero=is_index_global_attn_nonzero,
          is_local_index_global_attn_nonzero=is_local_index_global_attn_nonzero,
      )
    else:
      attn_output = self._sliding_chunks_matmul_attn_probs_value(
          attn_probs, value_vectors, self._one_sided_attn_window_size)

    if tf.executing_eagerly():
      tf.debugging.assert_equal(
          get_shape_list(attn_output),
          [batch_size, seq_len, self._num_heads, head_dim],
          message="Unexpected size",
      )

    attn_output = tf.reshape(
        attn_output,
        (batch_size, seq_len, self._num_heads * self._key_dim))  # FIXME

    # compute value for global attention and overwrite to attention output
    # TODO(crickwu): remove the redundant computation
    if self.global_attention_size > 0:
      attn_output, global_attn_probs = self._compute_global_attn_output_from_hidden(  # pylint: disable=unused-variable
          attn_output=attn_output,
          hidden_states=hidden_states,
          max_num_global_attn_indices=max_num_global_attn_indices,
          layer_head_mask=layer_head_mask,
          is_local_index_global_attn_nonzero=is_local_index_global_attn_nonzero,
          is_index_global_attn_nonzero=is_index_global_attn_nonzero,
          is_local_index_no_global_attn_nonzero=is_local_index_no_global_attn_nonzero,
          is_index_masked=is_index_masked,
          training=training,
      )
    else:
      global_attn_probs = tf.zeros(
          (batch_size, self._num_heads, max_num_global_attn_indices, seq_len))

    # make sure that local attention probabilities are set to 0 for indices of
    # global attn
    if self.global_attention_size > 0:
      masked_global_attn_index = tf.tile(
          is_index_global_attn[:, :, None, None],
          (1, 1, self._num_heads, self._one_sided_attn_window_size * 2 +
           max_num_global_attn_indices + 1),
      )
    else:
      masked_global_attn_index = tf.tile(
          is_index_global_attn[:, :, None, None],
          (1, 1, self._num_heads, self._one_sided_attn_window_size * 2 + 1),
      )

    attn_probs = tf.where(
        masked_global_attn_index,
        tf.zeros(
            get_shape_list(masked_global_attn_index), dtype=attn_probs.dtype),
        attn_probs,
    )

    # we can return extra information here
    # (attn_output, attn_probs, global_attn_probs)

    return attn_output