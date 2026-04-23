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

    if len(input_tensor_shape.as_list()) != 3:
      raise ValueError(
          "TransformerLayer expects a three-dimensional input of "
          "shape [batch, sequence, width]."
      )
    batch_size, sequence_length, hidden_size = input_tensor_shape

    if len(input_shape) == 2:
      mask_tensor_shape = tf.TensorShape(input_shape[1])
      expected_mask_tensor_shape = tf.TensorShape(
          [batch_size, sequence_length, sequence_length]
      )
      if not expected_mask_tensor_shape.is_compatible_with(mask_tensor_shape):
        raise ValueError(
            "When passing a mask tensor to TransformerLayer, the "
            "mask tensor must be of shape [batch, "
            "sequence_length, sequence_length] (here %s). Got a "
            "mask tensor of shape %s."
            % (expected_mask_tensor_shape, mask_tensor_shape)
        )
    if hidden_size % self._num_heads != 0:
      raise ValueError(
          "The input size (%d) is not a multiple of the number of attention "
          "heads (%d)" % (hidden_size, self._num_heads)
      )
    self._attention_head_size = int(hidden_size // self._num_heads)
    common_kwargs = dict(
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
        activity_regularizer=self._activity_regularizer,
        kernel_constraint=self._kernel_constraint,
        bias_constraint=self._bias_constraint,
    )
    attention_kwargs = dict(
        num_heads=self._num_heads,
        key_dim=self._attention_head_size,
        dropout=self._attention_dropout_rate,
        name="self_attention",
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
    )
    if self._src_block_size is not None:
      attention_kwargs.update(
          src_block_size=self._src_block_size,
          tgt_block_size=self._tgt_block_size,
          name="block_sparse_attention",
      )
      attention_fn = block_sparse_attention.MultiHeadAttention
    elif self._num_kv_heads is not None:
      attention_kwargs.update(
          num_kv_heads=self._num_kv_heads,
          name="multi_query_attention",
          )
      attention_fn = multi_query_attention.MultiHeadAttention
    else:
      attention_fn = tf_keras.layers.MultiHeadAttention
    self._attention_layer = attention_fn(**attention_kwargs, **common_kwargs)
    self._attention_dropout = tf_keras.layers.Dropout(rate=self._dropout_rate)
    if self._use_layer_norm:
      # Use float32 in layernorm for numeric stability.
      # It is probably safe in mixed_float16, but we haven't validated this yet.
      self._attention_layer_norm = tf_keras.layers.LayerNormalization(
          name="self_attention_layer_norm",
          axis=-1,
          epsilon=1e-12,
          dtype=tf.float32,
      )
    self._intermediate_dense = tf_keras.layers.EinsumDense(
        "abc,cd->abd",
        output_shape=(None, self._inner_dim),
        bias_axes="d",
        name="intermediate",
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        **common_kwargs)
    policy = tf_keras.mixed_precision.global_policy()
    if policy.name == "mixed_bfloat16":
      # bfloat16 causes BERT with the LAMB optimizer to not converge
      # as well, so we use float32.
      # TODO(b/154538392): Investigate this.
      policy = tf.float32
    self._inner_activation_layer = tf_keras.layers.Activation(
        self._inner_activation, dtype=policy)
    self._output_dense = tf_keras.layers.EinsumDense(
        "abc,cd->abd",
        output_shape=(None, hidden_size),
        bias_axes="d",
        name="output",
        kernel_initializer=tf_utils.clone_initializer(self._kernel_initializer),
        bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
        **common_kwargs)
    self._output_dropout = tf_keras.layers.Dropout(rate=self._dropout_rate)
    if self._use_layer_norm:
      # Use float32 in layernorm for numeric stability.
      self._output_layer_norm = tf_keras.layers.LayerNormalization(
          name="output_layer_norm", axis=-1, epsilon=1e-12, dtype=tf.float32)

    self._rezero_a = self.add_weight(
        name="rezero_alpha",
        initializer=tf_keras.initializers.Zeros(),
        trainable=True,
        dtype=tf.float32)

    if self._share_rezero:
      self._rezero_a_ffn = self._rezero_a
    else:
      self._rezero_a_ffn = self.add_weight(
          name="rezero_alpha_ffn",
          initializer=tf_keras.initializers.Zeros(),
          trainable=True,
          dtype=tf.float32)

    super().build(input_shape)