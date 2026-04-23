def add_weight(
        self,
        *args,
        shape=None,
        initializer=None,
        dtype=None,
        trainable=True,
        autocast=True,
        regularizer=None,
        constraint=None,
        aggregation="none",
        overwrite_with_gradient=False,
        name=None,
    ):
        """Add a weight variable to the layer.

        Args:
            shape: Shape tuple for the variable. Must be fully-defined
                (no `None` entries). Defaults to `()` (scalar) if unspecified.
            initializer: Initializer object to use to populate the initial
                variable value, or string name of a built-in initializer
                (e.g. `"random_normal"`). If unspecified, defaults to
                `"glorot_uniform"` for floating-point variables and to `"zeros"`
                for all other types (e.g. int, bool).
            dtype: Dtype of the variable to create, e.g. `"float32"`. If
                unspecified, defaults to the layer's variable dtype
                (which itself defaults to `"float32"` if unspecified).
            trainable: Boolean, whether the variable should be trainable via
                backprop or whether its updates are managed manually. Defaults
                to `True`.
            autocast: Boolean, whether to autocast layers variables when
                accessing them. Defaults to `True`.
            regularizer: Regularizer object to call to apply penalty on the
                weight. These penalties are summed into the loss function
                during optimization. Defaults to `None`.
            constraint: Contrainst object to call on the variable after any
                optimizer update, or string name of a built-in constraint.
                Defaults to `None`.
            aggregation: Optional string, one of `None`, `"none"`, `"mean"`,
                `"sum"` or `"only_first_replica"`. Annotates the variable with
                the type of multi-replica aggregation to be used for this
                variable when writing custom data parallel training loops.
                Defaults to `"none"`.
            overwrite_with_gradient: Boolean, whether to overwrite the variable
                with the computed gradient. This is useful for float8 training.
                Defaults to `False`.
            name: String name of the variable. Useful for debugging purposes.
        """
        self._check_super_called()
        if args:
            # `args` is only kept to detect the legacy Keras 2 call style
            # (`add_weight(shape, initializer, dtype, ...)`) and raise a clear
            # error for positional `name`.
            if len(args) > 3:
                raise TypeError(
                    "add_weight() takes at most 3 positional arguments "
                    f"but {len(args)} were given."
                )
            shape_arg = args[0]
            if isinstance(shape_arg, str):
                raise ValueError(
                    "`name` must be passed as a keyword argument. "
                    f"Received: add_weight('{shape_arg}', ...). "
                    f"Use: add_weight(shape=..., name='{shape_arg}')."
                )
            if shape is not None:
                raise ValueError(
                    "`shape` was passed both positionally and as "
                    "a keyword argument."
                )
            shape = shape_arg
            if len(args) > 1:
                if initializer is not None:
                    raise ValueError(
                        "`initializer` was passed both positionally and "
                        "as a keyword argument."
                    )
                initializer = args[1]
            if len(args) > 2:
                if dtype is not None:
                    raise ValueError(
                        "`dtype` was passed both positionally and as a "
                        "keyword argument."
                    )
                dtype = args[2]
        if shape is None:
            shape = ()
        if dtype is not None:
            dtype = backend.standardize_dtype(dtype)
        else:
            dtype = self.variable_dtype
        if initializer is None:
            if "float" in dtype:
                initializer = "glorot_uniform"
            else:
                initializer = "zeros"
        initializer = initializers.get(initializer)
        with backend.name_scope(self.name, caller=self):
            variable = backend.Variable(
                initializer=initializer,
                shape=shape,
                dtype=dtype,
                trainable=trainable,
                autocast=autocast,
                aggregation=aggregation,
                name=name,
            )
        # Will be added to layer.losses
        variable.regularizer = regularizers.get(regularizer)
        variable.constraint = constraints.get(constraint)
        variable.overwrite_with_gradient = overwrite_with_gradient
        self._track_variable(variable)
        return variable