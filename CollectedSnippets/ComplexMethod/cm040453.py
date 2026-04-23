def __init__(
        self,
        initializer,
        shape=None,
        dtype=None,
        trainable=True,
        autocast=True,
        aggregation="none",
        synchronization="auto",
        name=None,
        layout=None,
        **kwargs,
    ):
        name = name or auto_name(self.__class__.__name__)
        if not isinstance(name, str) or "/" in name:
            raise ValueError(
                "Argument `name` must be a string and "
                "cannot contain character `/`. "
                f"Received: name={name}"
            )
        if aggregation not in (
            None,
            "none",
            "mean",
            "sum",
            "only_first_replica",
        ):
            raise ValueError(
                "Invalid value for argument `aggregation`. Expected "
                "one of `None`, `'none'`, `'mean'`, `'sum'`, "
                "`'only_first_replica'`. "
                f"Received: aggregation={aggregation}"
            )
        if aggregation is None:
            aggregation = "none"
        if synchronization not in (
            None,
            "none",
            "on_read",
            "on_write",
            "auto",
        ):
            raise ValueError(
                "Invalid value for argument `synchronization`. Expected "
                "one of `None`, `'none'`, `'on_read'`, `'on_write'`, "
                "`'auto'`. "
                f"Received: synchronization={synchronization}"
            )
        if synchronization is None:
            synchronization = "none"
        self._name = name
        parent_path = current_path()
        if parent_path:
            self._path = f"{parent_path}/{name}"
        else:
            self._path = name
        self._shape = None
        self._initializer = None
        self._regularizer = None
        self._constraint = None
        self._trainable = bool(trainable)
        self._autocast = bool(autocast)
        self._aggregation = aggregation
        self._synchronization = synchronization
        self._layout = layout

        # `self._overwrite_with_gradient` is an internal property to determine
        # whether this variable should be overwritten by the computed gradient.
        # Ref: https://github.com/google/flax/blob/main/flax/linen/fp8_ops.py
        self._overwrite_with_gradient = False
        if isinstance(initializer, str):
            from keras.src import initializers

            initializer = initializers.get(initializer)
        if callable(initializer):
            if shape is None:
                raise ValueError(
                    "When creating a Variable from an initializer, "
                    "the `shape` argument should be specified. "
                    f"Received: initializer={initializer} "
                    f"and shape={shape}"
                )
        else:
            initializer = self._convert_to_tensor(initializer, dtype=dtype)
            # If dtype is None and `initializer` is an array, use its dtype.
            if dtype is None:
                dtype = initializer.dtype
        self._dtype = standardize_dtype(dtype)

        if in_stateless_scope():
            if callable(initializer):
                self._value = None
                self._initializer = initializer
                self._shape = self._validate_shape(shape)
                register_uninitialized_variable(self)
            else:
                raise ValueError(
                    "You are attempting to create a variable "
                    "while in a stateless scope. This is disallowed. "
                    "Make sure that all variables are created "
                    "before you start using your layer/model objects.\n\n"
                    "In some cases, you might be seeing this error "
                    "because you need to "
                    "implement a `def build(self, input_shape)` method "
                    "on your layer/model, which will "
                    "create its variables.\n\n"
                    "In some other cases, you might be seeing this error "
                    "because you are instantiating a `Variable` and "
                    "assigning it to a layer without going through "
                    "self.add_variable()/self.add_weight(). Always prefer "
                    "using these methods "
                    "(with a `shape` and `initializer` argument)."
                )
        else:
            if callable(initializer):
                self._shape = self._validate_shape(shape)
                self._initialize_with_initializer(initializer)
            else:
                self._initialize(initializer)
                self._shape = self._validate_shape(self._value.shape)
        self._ndim = len(self._shape)