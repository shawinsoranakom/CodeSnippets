def build(self, input_shape):
    if isinstance(input_shape, tf.TensorShape):
      input_tensor_shape = input_shape
    elif isinstance(input_shape, (list, tuple)):
      input_tensor_shape = tf.TensorShape(input_shape[0])
    else:
      raise ValueError(
          "The type of input shape argument is not supported, got: %s" %
          type(input_shape))

    if len(input_tensor_shape.as_list()) != 3:
      raise ValueError(
          "TransformerScaffold expects a three-dimensional input of "
          "shape [batch, sequence, width].")
    hidden_size = input_tensor_shape[-1]
    if hidden_size % self._num_heads != 0:
      raise ValueError(
          "The input size (%d) is not a multiple of the number of attention "
          "heads (%d)" % (hidden_size, self._num_heads))
    self._attention_head_size = int(hidden_size // self._num_heads)

    common_kwargs = dict(
        kernel_regularizer=self._kernel_regularizer,
        bias_regularizer=self._bias_regularizer,
        activity_regularizer=self._activity_regularizer,
        kernel_constraint=self._kernel_constraint,
        bias_constraint=self._bias_constraint)

    def get_layer_instance(instance_or_cls, config, default_config):
      if isinstance(instance_or_cls, tf_keras.layers.Layer):
        return instance_or_cls
      elif isinstance(instance_or_cls, dict):
        return get_layer_instance(
            tf_keras.utils.deserialize_keras_object(instance_or_cls),
            config,
            default_config,
        )
      else:
        if config is None:
          return instance_or_cls(**default_config)
        else:
          return instance_or_cls(**config)

    default_attention_cfg = {
        "kernel_initializer": tf_utils.clone_initializer(
            self._kernel_initializer),
        "bias_initializer": tf_utils.clone_initializer(self._bias_initializer),
        "num_heads": self._num_heads,
        "key_dim": self._attention_head_size,
        "dropout": self._attention_dropout_rate,
        "name": "self_attention"
    }
    default_attention_cfg.update(common_kwargs)
    self._attention_layer = get_layer_instance(
        self._attention_cls,
        config=self._attention_cfg,
        default_config=default_attention_cfg)

    if self._feedforward_cls is not None:
      default_feedforward_cfg = {
          "kernel_initializer": tf_utils.clone_initializer(
              self._kernel_initializer),
          "bias_initializer": tf_utils.clone_initializer(
              self._bias_initializer),
          "inner_dim": self._inner_dim,
          "inner_activation": self._inner_activation,
          # TODO(hongkuny): try to update all ffn block args.
          "intermediate_size": self._inner_dim,
          "intermediate_activation": self._inner_activation,
          "dropout": self._dropout_rate,
          "name": "feedforward",
      }
      default_feedforward_cfg.update(common_kwargs)
      self._feedforward_block = get_layer_instance(
          self._feedforward_cls,
          config=self._feedforward_cfg,
          default_config=default_feedforward_cfg)
    else:
      self._feedforward_block = None

    # self._dropout_rate controls dropout rates at two places:
    # after attention, and after FFN.
    self._attention_dropout = tf_keras.layers.Dropout(rate=self._dropout_rate)
    # Use float32 in layernorm for numeric stability.
    # It is probably safe in mixed_float16, but we haven't validated this yet.
    self._attention_layer_norm = (
        tf_keras.layers.LayerNormalization(
            name="self_attention_layer_norm",
            axis=-1,
            epsilon=self._norm_epsilon,
            dtype=tf.float32))

    if self._feedforward_block is None:
      self._intermediate_dense = tf_keras.layers.EinsumDense(
          "abc,cd->abd",
          output_shape=(None, self._inner_dim),
          bias_axes="d",
          name="intermediate",
          kernel_initializer=tf_utils.clone_initializer(
              self._kernel_initializer),
          bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
          **common_kwargs)
      policy = tf_keras.mixed_precision.global_policy()
      if policy.name == "mixed_bfloat16":
        # bfloat16 causes BERT with the LAMB optimizer to not converge
        # as well, so we use float32.
        # TODO(b/154538392): Investigate this.
        policy = tf.float32
      self._intermediate_activation_layer = tf_keras.layers.Activation(
          self._inner_activation, dtype=policy)
      self._output_dense = tf_keras.layers.EinsumDense(
          "abc,cd->abd",
          output_shape=(None, hidden_size),
          bias_axes="d",
          name="output",
          kernel_initializer=tf_utils.clone_initializer(
              self._kernel_initializer),
          bias_initializer=tf_utils.clone_initializer(self._bias_initializer),
          **common_kwargs)

    self._output_dropout = tf_keras.layers.Dropout(rate=self._dropout_rate)
    # Use float32 in layernorm for numeric stability.
    self._output_layer_norm = tf_keras.layers.LayerNormalization(
        name="output_layer_norm",
        axis=-1,
        epsilon=self._norm_epsilon,
        dtype=tf.float32)

    super().build(input_shape)
    logging.info("%s configs: %s", self.__class__.__name__, self.get_config())