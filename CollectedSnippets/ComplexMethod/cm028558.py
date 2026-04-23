def build(self, input_shape):
    if isinstance(input_shape, tf.TensorShape):
      input_tensor_shape = input_shape
    elif isinstance(input_shape, (list, tuple)):
      input_tensor_shape = tf.TensorShape(input_shape[0])
    else:
      raise ValueError(
          "The type of input shape argument is not supported, got: %s"
          % type(input_shape)
      )
    einsum_equation = "abc,cd->abd"
    if len(input_tensor_shape.as_list()) > 3:
      einsum_equation = "...bc,cd->...bd"
    hidden_size = input_tensor_shape[-1]
    if hidden_size % self._num_heads != 0:
      logging.warning(
          (
              "The input size (%d) is not a multiple of the number of attention"
              " heads (%d)"
          ),
          hidden_size,
          self._num_heads,
      )
    if self._key_dim is None:
      self._key_dim = int(hidden_size // self._num_heads)
    if self._output_last_dim is None:
      last_output_shape = hidden_size
    else:
      last_output_shape = self._output_last_dim

    common_kwargs = dict(
        bias_regularizer=self._bias_regularizer,
        activity_regularizer=self._activity_regularizer,
        kernel_constraint=self._kernel_constraint,
        bias_constraint=self._bias_constraint,
    )
    self._key_projection = tf_keras.layers.Dense(
        self._low_rank_features,
        activation=None,
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        name="key_low_rank_projection",
        **common_kwargs
    )
    self._value_projection = tf_keras.layers.Dense(
        self._low_rank_features,
        activation=None,
        use_bias=False,
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        name="value_low_rank_projection",
        **common_kwargs
    )
    self._attention_layer = tf_keras.layers.MultiHeadAttention(
        num_heads=self._num_heads,
        key_dim=self._low_rank_features,
        value_dim=self._low_rank_features,
        dropout=self._attention_dropout_rate,
        use_bias=self._use_bias,
        kernel_initializer=self._attention_initializer,
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        attention_axes=self._attention_axes,
        output_shape=self._output_last_dim,
        name="self_attention",
        **common_kwargs
    )
    self._attention_dropout = tf_keras.layers.Dropout(
        rate=self._attention_dropout_rate
    )
    # Use float32 in layernorm for numeric stability.
    # It is probably safe in mixed_float16, but we haven't validated this yet.
    self._attention_layer_norm = tf_keras.layers.LayerNormalization(
        name="self_attention_layer_norm",
        axis=-1,
        epsilon=self._norm_epsilon,
        dtype=tf.float32,
    )
    self._attention_layer_norm_kv = self._attention_layer_norm
    if self._diff_q_kv_att_layer_norm:
      self._attention_layer_norm_kv = tf_keras.layers.LayerNormalization(
          name="self_attention_layer_norm_kv",
          axis=-1,
          epsilon=self._norm_epsilon,
          dtype=tf.float32,
      )

    self._intermediate_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=(None, self._inner_dim),
        bias_axes="d",
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        name="intermediate",
        **common_kwargs
    )
    policy = tf_keras.mixed_precision.global_policy()
    if policy.name == "mixed_bfloat16":
      # bfloat16 causes BERT with the LAMB optimizer to not converge
      # as well, so we use float32.
      # TODO(b/154538392): Investigate this.
      policy = tf.float32
    self._intermediate_activation_layer = tf_keras.layers.Activation(
        self._inner_activation, dtype=policy
    )
    self._inner_dropout_layer = tf_keras.layers.Dropout(
        rate=self._inner_dropout
    )
    self._output_dense = tf_keras.layers.EinsumDense(
        einsum_equation,
        output_shape=(None, last_output_shape),
        bias_axes="d",
        name="output",
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        **common_kwargs
    )
    self._output_dropout = tf_keras.layers.Dropout(
        rate=self._output_dropout_rate
    )
    # Use float32 in layernorm for numeric stability.
    self._output_layer_norm = tf_keras.layers.LayerNormalization(
        name="output_layer_norm",
        axis=-1,
        epsilon=self._norm_epsilon,
        dtype=tf.float32,
    )

    super().build(input_shape)