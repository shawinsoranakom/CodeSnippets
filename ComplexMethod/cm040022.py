def __init__(
        self,
        num_bins,
        mask_value=None,
        salt=None,
        output_mode="int",
        sparse=False,
        **kwargs,
    ):
        if not tf.available:
            raise ImportError(
                "Layer Hashing requires TensorFlow. "
                "Install it via `pip install tensorflow`."
            )

        # By default, output int32 when output_mode='int' and floats otherwise.
        if "dtype" not in kwargs or kwargs["dtype"] is None:
            kwargs["dtype"] = (
                "int64" if output_mode == "int" else backend.floatx()
            )

        super().__init__(**kwargs)

        if num_bins is None or num_bins <= 0:
            raise ValueError(
                "The `num_bins` for `Hashing` cannot be `None` or "
                f"non-positive values. Received: num_bins={num_bins}."
            )

        if output_mode == "int" and (
            self.dtype_policy.name not in ("int32", "int64")
        ):
            raise ValueError(
                'When `output_mode="int"`, `dtype` should be an integer '
                f"type, 'int32' or 'in64'. Received: dtype={kwargs['dtype']}"
            )

        # 'output_mode' must be one of (INT, ONE_HOT, MULTI_HOT, COUNT)
        accepted_output_modes = ("int", "one_hot", "multi_hot", "count")
        if output_mode not in accepted_output_modes:
            raise ValueError(
                "Invalid value for argument `output_mode`. "
                f"Expected one of {accepted_output_modes}. "
                f"Received: output_mode={output_mode}"
            )

        if sparse and output_mode == "int":
            raise ValueError(
                "`sparse` may only be true if `output_mode` is "
                '`"one_hot"`, `"multi_hot"`, or `"count"`. '
                f"Received: sparse={sparse} and "
                f"output_mode={output_mode}"
            )

        self.num_bins = num_bins
        self.mask_value = mask_value
        self.strong_hash = True if salt is not None else False
        self.output_mode = output_mode
        self.sparse = sparse
        self.salt = None
        if salt is not None:
            if isinstance(salt, (tuple, list)) and len(salt) == 2:
                self.salt = list(salt)
            elif isinstance(salt, int):
                self.salt = [salt, salt]
            else:
                raise ValueError(
                    "The `salt` argument for `Hashing` can only be a tuple of "
                    "size 2 integers, or a single integer. "
                    f"Received: salt={salt}."
                )
        self._convert_input_args = False
        self._allow_non_tensor_positional_args = True
        self.supports_jit = False