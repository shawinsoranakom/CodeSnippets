def __init__(
        self,
        num_heads,
        key_dim,
        value_dim=None,
        dropout=0.0,
        use_bias=True,
        output_shape=None,
        attention_axes=None,
        flash_attention=None,
        kernel_initializer="glorot_uniform",
        bias_initializer="zeros",
        kernel_regularizer=None,
        bias_regularizer=None,
        activity_regularizer=None,
        kernel_constraint=None,
        bias_constraint=None,
        use_gate=False,
        seed=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.supports_masking = True
        self._num_heads = num_heads
        self._key_dim = key_dim
        self._value_dim = value_dim if value_dim else key_dim
        self._dropout = dropout
        self._use_bias = use_bias
        self._use_gate = use_gate
        if output_shape:
            if isinstance(output_shape, int):
                output_shape = (output_shape,)
            try:
                output_shape = tuple(output_shape)
            except:
                raise ValueError(
                    f"Invalid `output_shape`: {output_shape}. When "
                    "specified, the `output_shape` should be of type tuple, "
                    "list, or int."
                )
        self._output_shape = output_shape
        self._flash_attention = flash_attention or is_flash_attention_enabled()
        self._kernel_initializer = initializers.get(kernel_initializer)
        self._bias_initializer = initializers.get(bias_initializer)
        self._kernel_regularizer = regularizers.get(kernel_regularizer)
        self._bias_regularizer = regularizers.get(bias_regularizer)
        self._activity_regularizer = regularizers.get(activity_regularizer)
        self._kernel_constraint = constraints.get(kernel_constraint)
        self._bias_constraint = constraints.get(bias_constraint)
        if isinstance(attention_axes, int):
            attention_axes = (attention_axes,)
        elif attention_axes and not isinstance(attention_axes, (list, tuple)):
            raise ValueError(
                "`attention_axes` must be an int, list, or tuple."
                f"Received: attention_axes={attention_axes}"
            )
        self._attention_axes = attention_axes
        self.seed = seed

        self._inverse_sqrt_key_dim = 1.0 / math.sqrt(float(self._key_dim))

        # Check for flash attention constraints
        if self._flash_attention and self._dropout > 0.0:
            raise ValueError(
                "Dropout is not supported when flash attention is enabled. "
                "Please set dropout to 0.0 to use flash attention."
            )