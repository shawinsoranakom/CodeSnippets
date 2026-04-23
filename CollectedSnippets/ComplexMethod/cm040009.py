def __init__(
        self,
        max_tokens=None,
        num_oov_indices=1,
        mask_token=None,
        oov_token=-1,
        vocabulary=None,
        vocabulary_dtype="int64",
        idf_weights=None,
        invert=False,
        output_mode="int",
        sparse=False,
        pad_to_max_tokens=False,
        oov_method="floormod",
        salt=None,
        name=None,
        **kwargs,
    ):
        if not tf.available:
            raise ImportError(
                "Layer IntegerLookup requires TensorFlow. "
                "Install it via `pip install tensorflow`."
            )
        if max_tokens is not None and max_tokens <= 1:
            raise ValueError(
                "If `max_tokens` is set for `IntegerLookup`, it must be "
                f"greater than 1. Received: max_tokens={max_tokens}"
            )
        if num_oov_indices < 0:
            raise ValueError(
                "The value of `num_oov_indices` argument for `IntegerLookup` "
                "must >= 0. Received: num_oov_indices="
                f"{num_oov_indices}"
            )
        if sparse and backend.backend() != "tensorflow":
            raise ValueError(
                "`sparse=True` can only be used with the TensorFlow backend."
            )
        if vocabulary_dtype != "int64":
            raise ValueError(
                "Only `vocabulary_dtype='int64'` is supported "
                "at this time. Received: "
                f"vocabulary_dtype={vocabulary_dtype}"
            )
        super().__init__(
            max_tokens=max_tokens,
            num_oov_indices=num_oov_indices,
            mask_token=mask_token,
            oov_token=oov_token,
            vocabulary=vocabulary,
            vocabulary_dtype=vocabulary_dtype,
            idf_weights=idf_weights,
            invert=invert,
            output_mode=output_mode,
            sparse=sparse,
            pad_to_max_tokens=pad_to_max_tokens,
            oov_method=oov_method,
            salt=salt,
            name=name,
            **kwargs,
        )
        self._convert_input_args = False
        self._allow_non_tensor_positional_args = True
        self.supports_jit = False