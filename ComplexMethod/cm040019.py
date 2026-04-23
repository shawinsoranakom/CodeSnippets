def __init__(
        self,
        max_tokens=None,
        standardize="lower_and_strip_punctuation",
        split="whitespace",
        ngrams=None,
        output_mode="int",
        output_sequence_length=None,
        pad_to_max_tokens=False,
        vocabulary=None,
        idf_weights=None,
        sparse=False,
        ragged=False,
        encoding="utf-8",
        name=None,
        **kwargs,
    ):
        if not tf.available:
            raise ImportError(
                "Layer TextVectorization requires TensorFlow. "
                "Install it via `pip install tensorflow`."
            )
        if sparse and backend.backend() != "tensorflow":
            raise ValueError(
                "`sparse=True` can only be used with the TensorFlow backend."
            )
        if ragged and backend.backend() != "tensorflow":
            raise ValueError(
                "`ragged=True` can only be used with the TensorFlow backend."
            )

        # 'standardize' must be one of
        # (None, "lower_and_strip_punctuation", "lower", "strip_punctuation",
        # callable)
        argument_validation.validate_string_arg(
            standardize,
            allowable_strings=(
                "lower_and_strip_punctuation",
                "lower",
                "strip_punctuation",
            ),
            caller_name=self.__class__.__name__,
            arg_name="standardize",
            allow_none=True,
            allow_callables=True,
        )

        # 'split' must be one of (None, "whitespace", "character", callable)
        argument_validation.validate_string_arg(
            split,
            allowable_strings=("whitespace", "character"),
            caller_name=self.__class__.__name__,
            arg_name="split",
            allow_none=True,
            allow_callables=True,
        )

        # Support deprecated names for output_modes.
        if output_mode == "binary":
            output_mode = "multi_hot"
        if output_mode == "tf-idf":
            output_mode = "tf_idf"
        argument_validation.validate_string_arg(
            output_mode,
            allowable_strings=(
                "int",
                "one_hot",
                "multi_hot",
                "count",
                "tf_idf",
            ),
            caller_name=self.__class__.__name__,
            arg_name="output_mode",
        )

        # 'ngrams' must be one of (None, int, tuple(int))
        if not (
            ngrams is None
            or isinstance(ngrams, int)
            or isinstance(ngrams, tuple)
            and all(isinstance(item, int) for item in ngrams)
        ):
            raise ValueError(
                "`ngrams` must be None, an integer, or a tuple of "
                f"integers. Received: ngrams={ngrams}"
            )

        # 'output_sequence_length' must be one of (None, int) and is only
        # set if output_mode is "int"".
        if output_mode == "int" and not (
            isinstance(output_sequence_length, int)
            or (output_sequence_length is None)
        ):
            raise ValueError(
                "`output_sequence_length` must be either None or an "
                "integer when `output_mode` is 'int'. Received: "
                f"output_sequence_length={output_sequence_length}"
            )

        if output_mode != "int" and output_sequence_length is not None:
            raise ValueError(
                "`output_sequence_length` must not be set if `output_mode` is "
                "not 'int'. "
                f"Received output_sequence_length={output_sequence_length}."
            )

        if ragged and output_mode != "int":
            raise ValueError(
                "`ragged` must not be true if `output_mode` is "
                f"`'int'`. Received: ragged={ragged} and "
                f"output_mode={output_mode}"
            )

        self._max_tokens = max_tokens
        self._standardize = standardize
        self._split = split
        self._ngrams_arg = ngrams
        if isinstance(ngrams, int):
            self._ngrams = tuple(range(1, ngrams + 1))
        else:
            self._ngrams = ngrams
        self._ragged = ragged

        self._output_mode = output_mode
        self._output_sequence_length = output_sequence_length
        self._encoding = encoding

        # We save this hidden option to persist the fact
        # that we have a non-adaptable layer with a
        # manually set vocab.
        self._has_input_vocabulary = kwargs.pop(
            "has_input_vocabulary", (vocabulary is not None)
        )
        vocabulary_size = kwargs.pop("vocabulary_size", None)

        super().__init__(name=name, **kwargs)

        self._lookup_layer = StringLookup(
            max_tokens=max_tokens,
            vocabulary=vocabulary,
            idf_weights=idf_weights,
            pad_to_max_tokens=pad_to_max_tokens,
            mask_token="",
            output_mode=output_mode,
            sparse=sparse,
            has_input_vocabulary=self._has_input_vocabulary,
            encoding=encoding,
            vocabulary_size=vocabulary_size,
        )
        self._convert_input_args = False
        self._allow_non_tensor_positional_args = True
        self.supports_jit = False