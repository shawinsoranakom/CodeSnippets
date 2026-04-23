def __init__(self,
               num_heads,
               key_dim,
               value_dim=None,
               dropout=0.0,
               reuse_attention=0,
               use_relative_pe=False,
               pe_max_seq_length=512,
               use_bias=True,
               output_shape=None,
               attention_axes=None,
               kernel_initializer="glorot_uniform",
               bias_initializer="zeros",
               kernel_regularizer=None,
               bias_regularizer=None,
               activity_regularizer=None,
               kernel_constraint=None,
               bias_constraint=None,
               **kwargs):
    super().__init__(**kwargs)
    self._num_heads = num_heads
    self._key_dim = key_dim
    self._value_dim = value_dim if value_dim else key_dim
    self._dropout = dropout
    if reuse_attention > self._num_heads or reuse_attention < -1:
      raise ValueError("reuse_attention should be between -1 "
                       "and %d in call to %s." % (self.__class__,
                                                  self._num_heads))
    if reuse_attention == -1:
      reuse_attention = self._num_heads
    self._reuse_heads = reuse_attention
    self._use_relative_pe = use_relative_pe
    self._pe_max_seq_length = pe_max_seq_length
    self._use_bias = use_bias
    self._output_shape = output_shape
    self._kernel_initializer = tf_keras.initializers.get(kernel_initializer)
    self._bias_initializer = tf_keras.initializers.get(bias_initializer)
    self._kernel_regularizer = tf_keras.regularizers.get(kernel_regularizer)
    self._bias_regularizer = tf_keras.regularizers.get(bias_regularizer)
    self._kernel_constraint = tf_keras.constraints.get(kernel_constraint)
    self._bias_constraint = tf_keras.constraints.get(bias_constraint)
    if attention_axes is not None and not isinstance(attention_axes,
                                                     collections.abc.Sized):
      self._attention_axes = (attention_axes,)
    else:
      self._attention_axes = attention_axes
    self._built_from_signature = False
    self._query_shape, self._key_shape, self._value_shape = None, None, None
    # Use relative PE only if reuse_heads < num_heads.
    if self._use_relative_pe and self._reuse_heads < self._num_heads:
      # Determine the dtype from global policy.
      policy = tf_keras.mixed_precision.global_policy()
      if policy.name == "mixed_bfloat16":
        policy = tf.bfloat16
      elif policy.name == "mixed_float16":
        policy = tf.float16
      else:
        policy = tf.float32
      self._position_embeddings = tf.Variable(
          name="relative_position_embeddings",
          initial_value=lambda: tf.random.truncated_normal(  # pylint: disable=g-long-lambda
              [
                  1, self._num_heads - self._reuse_heads, 2 * self.
                  _pe_max_seq_length - 1
              ], mean=0.0, stddev=0.2, dtype=policy),
          trainable=True, dtype=policy)