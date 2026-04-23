def __init__(
        self,
        rank,
        filters,
        kernel_size,
        strides=1,
        padding="valid",
        output_padding=None,
        data_format=None,
        dilation_rate=1,
        activation=None,
        use_bias=True,
        kernel_initializer="glorot_uniform",
        bias_initializer="zeros",
        kernel_regularizer=None,
        bias_regularizer=None,
        activity_regularizer=None,
        kernel_constraint=None,
        bias_constraint=None,
        trainable=True,
        name=None,
        **kwargs,
    ):
        super().__init__(
            trainable=trainable,
            name=name,
            activity_regularizer=activity_regularizer,
            **kwargs,
        )
        self.rank = rank
        self.filters = filters
        self.kernel_size = standardize_tuple(kernel_size, rank, "kernel_size")
        self.strides = standardize_tuple(strides, rank, "strides")
        self.dilation_rate = standardize_tuple(
            dilation_rate, rank, "dilation_rate"
        )
        self.padding = standardize_padding(padding)
        if output_padding is None:
            self.output_padding = None
        else:
            self.output_padding = standardize_tuple(
                output_padding,
                rank,
                "output_padding",
                allow_zero=True,
            )
        self.data_format = standardize_data_format(data_format)
        self.activation = activations.get(activation)
        self.use_bias = use_bias
        self.kernel_initializer = initializers.get(kernel_initializer)
        self.bias_initializer = initializers.get(bias_initializer)
        self.kernel_regularizer = regularizers.get(kernel_regularizer)
        self.bias_regularizer = regularizers.get(bias_regularizer)
        self.kernel_constraint = constraints.get(kernel_constraint)
        self.bias_constraint = constraints.get(bias_constraint)
        self.input_spec = InputSpec(min_ndim=self.rank + 2)
        self.data_format = self.data_format

        if self.filters is not None and self.filters <= 0:
            raise ValueError(
                "Invalid value for argument `filters`. Expected a strictly "
                f"positive value. Received filters={self.filters}."
            )

        if not all(self.kernel_size):
            raise ValueError(
                "The argument `kernel_size` cannot contain 0. Received "
                f"kernel_size={self.kernel_size}."
            )

        if not all(self.strides):
            raise ValueError(
                "The argument `strides` cannot contains 0. Received "
                f"strides={self.strides}."
            )

        if self.output_padding is not None:
            for i, (op, s) in enumerate(zip(self.output_padding, self.strides)):
                if op >= s:
                    raise ValueError(
                        "`output_padding` must be strictly less than "
                        f"`strides` for all dimensions. At dimension {i}, "
                        f"`output_padding` is {op} but `strides` is {s}. "
                        f"Received: output_padding={self.output_padding}, "
                        f"strides={self.strides}"
                    )

        if max(self.strides) > 1 and max(self.dilation_rate) > 1:
            raise ValueError(
                "`strides > 1` not supported in conjunction with "
                f"`dilation_rate > 1`. Received: strides={self.strides} and "
                f"dilation_rate={self.dilation_rate}"
            )

        if self.output_padding is not None:
            for i, (op, s) in enumerate(zip(self.output_padding, self.strides)):
                if op >= s:
                    raise ValueError(
                        "Invalid `output_padding` argument. "
                        "Each value in `output_padding` must be strictly "
                        "less than the corresponding `strides` value.\n"
                        f"At index {i}, `output_padding` is {op} and `strides` "
                        f"is {s}.\n"
                        f"Received: output_padding={self.output_padding}, "
                        f"strides={self.strides}."
                    )