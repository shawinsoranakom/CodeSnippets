def _build_from_signature(self, query, value, key=None):
    """Builds layers and variables.

    Once the method is called, self._built_from_signature will be set to True.
    Args:
      query: Query tensor or TensorShape.
      value: Value tensor or TensorShape.
      key: Key tensor or TensorShape.
    """
    self._built_from_signature = True
    if hasattr(query, "shape"):
      self._query_shape = tf.TensorShape(query.shape)
    else:
      self._query_shape = tf.TensorShape(query)
    if hasattr(value, "shape"):
      self._value_shape = tf.TensorShape(value.shape)
    else:
      self._value_shape = tf.TensorShape(value)
    if key is None:
      self._key_shape = self._value_shape
    elif hasattr(key, "shape"):
      self._key_shape = tf.TensorShape(key.shape)
    else:
      self._key_shape = tf.TensorShape(key)

    common_kwargs = dict(
        kernel_initializer=self._kernel_initializer,
        bias_initializer=self._bias_initializer,
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
        activity_regularizer=self._activity_regularizer,
        kernel_constraint=self._kernel_constraint,
        bias_constraint=self._bias_constraint)
    # Any setup work performed only once should happen in an `init_scope`
    # to avoid creating symbolic Tensors that will later pollute any eager
    # operations.
    # with tf_utils.maybe_init_scope(self):
    # TODO(crickwu): check whether tf_utils.maybe_init_scope(self) (keras)
    # is needed.
    free_dims = self._query_shape.rank - 1
    einsum_equation, bias_axes, output_rank = _build_proj_equation(
        free_dims, bound_dims=1, output_dims=2)
    self._query_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._key_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="query",
        **common_kwargs)
    self._global_query_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._key_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="global_query",
        **common_kwargs)
    einsum_equation, bias_axes, output_rank = _build_proj_equation(
        self._key_shape.rank - 1, bound_dims=1, output_dims=2)
    self._key_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._key_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="key",
        **common_kwargs)
    self._global_key_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._key_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="global_key",
        **common_kwargs)
    einsum_equation, bias_axes, output_rank = _build_proj_equation(
        self._value_shape.rank - 1, bound_dims=1, output_dims=2)
    self._value_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._value_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="value",
        **common_kwargs)
    self._global_value_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=_get_output_shape(output_rank - 1,
                                       [self._num_heads, self._value_dim]),
        bias_axes=bias_axes if self._use_bias else None,
        name="global_value",
        **common_kwargs)

    # Builds the attention computations for multi-head dot product attention.
    # These computations could be wrapped into the keras attention layer once
    # it support mult-head einsum computations.
    self._build_attention(output_rank)
    self._global_dropout_layer = tf_keras.layers.Dropout(rate=self._dropout)
    # self._output_dense = self._make_output_dense(
    #   free_dims, common_kwargs, "attention_output")
    self._output_dense = tf_keras.layers.Dense(
        units=self._num_heads * self._key_dim, name="dense", **common_kwargs)