def __init__(
        self,
        max_tokens,
        num_oov_indices,
        mask_token,
        oov_token,
        vocabulary_dtype,
        vocabulary=None,
        idf_weights=None,
        invert=False,
        output_mode="int",
        sparse=False,
        pad_to_max_tokens=False,
        oov_method="floormod",
        name=None,
        salt=None,
        **kwargs,
    ):
        # If max_tokens is set, the value must be greater than 1 - otherwise we
        # are creating a 0-element vocab, which doesn't make sense.
        if max_tokens is not None and max_tokens <= 1:
            raise ValueError(
                "If set, `max_tokens` must be greater than 1. "
                f"Received: max_tokens={max_tokens}"
            )

        if pad_to_max_tokens and max_tokens is None:
            raise ValueError(
                "If pad_to_max_tokens is True, must set `max_tokens`. "
                f"Received: max_tokens={max_tokens}"
            )

        if num_oov_indices < 0:
            raise ValueError(
                "`num_oov_indices` must be greater than or equal to 0. "
                f"Received: num_oov_indices={num_oov_indices}"
            )

        argument_validation.validate_string_arg(
            oov_method,
            allowable_strings=("floormod", "farmhash"),
            caller_name=self.__class__.__name__,
            arg_name="oov_method",
        )

        if salt is not None:
            if (
                tf.as_dtype(vocabulary_dtype).is_integer
                and oov_method != "farmhash"
            ):
                raise ValueError(
                    "`salt` can only be used when `oov_method='farmhash'`. "
                    f"Received: oov_method={oov_method}"
                )
            if isinstance(salt, (tuple, list)) and len(salt) == 2:
                salt = list(salt)
            elif isinstance(salt, int):
                salt = [salt, salt]
            else:
                raise ValueError(
                    "The `salt` argument for `IndexLookup` can only be a tuple "
                    "of 2 integers, or a single integer. "
                    f"Received: salt={salt}."
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

        if invert and output_mode != "int":
            raise ValueError(
                "`output_mode` must be `'int'` when `invert` is true. "
                f"Received: output_mode={output_mode}"
            )

        if sparse and output_mode == "int":
            raise ValueError(
                "`sparse` may only be true if `output_mode` is "
                "`'one_hot'`, `'multi_hot'`, `'count'` or `'tf_idf'`. "
                f"Received: sparse={sparse} and "
                f"output_mode={output_mode}"
            )

        if idf_weights is not None and output_mode != "tf_idf":
            raise ValueError(
                "`idf_weights` should only be set if `output_mode` is "
                f"`'tf_idf'`. Received: idf_weights={idf_weights} and "
                f"output_mode={output_mode}"
            )

        super().__init__(name=name)
        self._convert_input_args = False
        self._allow_non_tensor_positional_args = True
        self.supports_jit = False

        self.invert = invert
        self.max_tokens = max_tokens
        self.num_oov_indices = num_oov_indices
        self.mask_token = mask_token
        self.oov_token = oov_token
        self.output_mode = output_mode
        self.sparse = sparse
        self.pad_to_max_tokens = pad_to_max_tokens
        self.vocabulary_dtype = tf.as_dtype(vocabulary_dtype).name
        self.oov_method = oov_method
        self.salt = salt
        self._frozen_vocab_size = kwargs.pop("vocabulary_size", None)

        # Remember original `vocabulary` as `input_vocabulary` for serialization
        # via `get_config`. However, if `vocabulary` is a file path or a URL, we
        # serialize the vocabulary as an asset and clear the original path/URL.
        self.input_vocabulary = (
            vocabulary if not isinstance(vocabulary, str) else None
        )
        self.input_idf_weights = idf_weights

        # We set this hidden attr to
        # persist the fact that we have have a non-adaptable layer with a
        # manually set vocab.
        self._has_input_vocabulary = kwargs.pop(
            "has_input_vocabulary", (vocabulary is not None)
        )
        kwargs.pop("trainable", None)
        kwargs.pop("dtype", None)
        if kwargs:
            raise ValueError(f"Unrecognized keyword argument(s): {kwargs}")

        if invert:
            self._key_dtype = "int64"
            self._value_dtype = self.vocabulary_dtype
            mask_key = 0
            mask_value = mask_token
            self._default_value = self.oov_token
        else:
            self._key_dtype = self.vocabulary_dtype
            self._value_dtype = "int64"
            mask_key = mask_token
            # Masks should map to 0 for int output and be dropped otherwise. Max
            # ints will be dropped from the bincount op.
            mask_value = (
                0
                if self.output_mode == "int"
                else tf.as_dtype(self._value_dtype).max
            )
            if self.num_oov_indices == 0:
                # If there are no OOV indices, we map OOV tokens to -1 and error
                # out during call if we find a negative index.
                self._default_value = -1
            elif self.num_oov_indices == 1:
                # If there is only one OOV index, we can set that index as the
                # default value of the index_lookup table.
                self._default_value = self._oov_start_index()
            else:
                # If we have multiple OOV values, we need to do a further
                # hashing step; to make this easier, we set the OOV value to -1.
                # (This lets us do a vectorized add and cast to boolean to
                # determine locations where we need to do extra hashing.)
                self._default_value = -1
        if self.mask_token is not None:
            self._mask_key = tf.convert_to_tensor(mask_key, self._key_dtype)
            self._mask_value = tf.convert_to_tensor(
                mask_value, self._value_dtype
            )

        if self.output_mode == "tf_idf":
            if self._has_input_vocabulary and idf_weights is None:
                raise ValueError(
                    "When specifying the `vocabulary` argument, "
                    "in TF-IDF output mode, the `idf_weights` argument "
                    "must also be provided."
                )
            if idf_weights is not None:
                self.idf_weights = tf.Variable(
                    idf_weights,
                    dtype=backend.floatx(),
                    trainable=False,
                )
                self.idf_weights_const = self.idf_weights.value()

        if vocabulary is not None:
            self.set_vocabulary(vocabulary, idf_weights)
        else:
            # When restoring from a keras SavedModel, the loading code will
            # expect to find and restore a lookup_table attribute on the layer.
            # This table needs to be uninitialized as a StaticHashTable cannot
            # be initialized twice.
            self.lookup_table = self._uninitialized_lookup_table()

        # Only set up adapt state if we did not receive a vocab on construction.
        if not self._has_input_vocabulary:
            # Set adapt state.
            self.token_counts = tf.lookup.experimental.MutableHashTable(
                key_dtype=vocabulary_dtype,
                value_dtype="int64",
                default_value=0,
            )
            if self.output_mode == "tf_idf":
                self.token_document_counts = (
                    tf.lookup.experimental.MutableHashTable(
                        key_dtype=vocabulary_dtype,
                        value_dtype="int64",
                        default_value=0,
                    )
                )
                self.num_documents = tf.Variable(
                    0, dtype="int64", trainable=False
                )