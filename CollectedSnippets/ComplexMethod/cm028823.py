def _compute_attention(
      self,
      query: tf.Tensor,
      key: tf.Tensor,
      value: tf.Tensor,
      attention_mask: Optional[tf.Tensor] = None,
      training: Optional[bool] = None,
  ):
    """Applies dot-product attention with query, key, value tensors.

    Args:
      query: Projected query `Tensor` of shape `(B, T, N, key_dim)`.
      key: Projected key `Tensor` of shape `(B, S, N, key_dim)`.
      value: Projected value `Tensor` of shape `(B, S, N, value_dim)`.
      attention_mask: a boolean mask of shape `(B, T, S)`, that prevents
        attention to certain positions. It is generally not needed if the
        `query` and `value` (and/or `key`) are masked.
      training: Python boolean indicating whether the layer should behave in
        training mode (adding dropout) or in inference mode (doing nothing).

    Returns:
      attention_output: Multi-headed outputs of attention computation.
      attention_scores: Multi-headed attention weights.
    """
    if self._partition_dims is not None:
      strategy = tf.distribute.get_strategy()
      # `query` = [B, T, N ,H]
      query = strategy.experimental_split_to_logical_devices(
          query, self._partition_dims)
      key = strategy.experimental_split_to_logical_devices(
          key, self._partition_dims)
      value = strategy.experimental_split_to_logical_devices(
          value, self._partition_dims)

    batch_size = query.get_shape().as_list()[0]  # None if dynamic.

    if (
        training
        or self._max_inference_parallelism is None
        or self._max_inference_parallelism <= 0
        or (
            # If the whole batch is allowed to be run in parallel, use fully
            # vectorized computation instead of tf.map_fn to make things more
            # efficient.
            batch_size is not None
            and batch_size <= self._max_inference_parallelism
        )
    ):
      return self._compute_attention_delegate(
          query, key, value, attention_mask, training
      )
    else:
      # Sequentialize the inference execution with limited parallelism.
      def _compute_fn(x):
        attention_output, attention_scores = self._compute_attention_delegate(
            query=x[0][tf.newaxis, ...],
            key=x[1][tf.newaxis, ...],
            value=x[2][tf.newaxis, ...],
            attention_mask=x[3][tf.newaxis, ...] if len(x) >= 4 else None,
            training=training,
        )
        attention_output = tf.squeeze(attention_output, axis=0)
        attention_scores = tf.squeeze(attention_scores, axis=0)
        return attention_output, attention_scores

      if attention_mask is not None:
        elems = [query, key, value, attention_mask]
      else:
        elems = [query, key, value]

      return tf.map_fn(
          fn=_compute_fn,
          elems=elems,
          fn_output_signature=(value.dtype, value.dtype),
          parallel_iterations=self._max_inference_parallelism,
      )