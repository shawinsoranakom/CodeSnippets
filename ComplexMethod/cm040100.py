def __init__(
        self,
        shape=None,
        batch_size=None,
        dtype=None,
        sparse=None,
        ragged=None,
        batch_shape=None,
        input_tensor=None,
        optional=False,
        name=None,
        **kwargs,
    ):
        super().__init__(name=name)

        if "input_shape" in kwargs:
            warnings.warn(
                "Argument `input_shape` is deprecated. Use `shape` instead."
            )
            shape = kwargs.pop("input_shape")
        if "batch_input_shape" in kwargs:
            batch_shape = kwargs.pop("batch_input_shape")

        if input_tensor is not None:
            if not isinstance(input_tensor, backend.KerasTensor):
                raise ValueError(
                    "Argument `input_tensor` must be a KerasTensor. "
                    f"Received invalid type: input_tensor={input_tensor} "
                    f"(of type {type(input_tensor)})"
                )
            if batch_size is not None:
                if (
                    len(input_tensor.shape) < 1
                    or input_tensor.shape[0] != batch_size
                ):
                    raise ValueError(
                        "When providing the `input_tensor` argument, you "
                        "cannot provide an incompatible `batch_size` argument."
                    )
            if shape is not None:
                if (
                    len(shape) != len(input_tensor.shape) - 1
                    or shape != input_tensor.shape[1:]
                ):
                    raise ValueError(
                        "When providing the `input_tensor` argument, you "
                        "cannot provide an incompatible `shape` argument."
                    )
            if batch_shape is not None and batch_shape != input_tensor.shape:
                raise ValueError(
                    "When providing the `input_tensor` argument, you "
                    "cannot provide an incompatible `batch_shape` argument."
                )
            if dtype is not None and input_tensor.dtype != dtype:
                raise ValueError(
                    "When providing the `input_tensor` argument, you "
                    "cannot provide an incompatible `dtype` argument."
                )
            if sparse is not None and input_tensor.sparse != sparse:
                raise ValueError(
                    "When providing the `input_tensor` argument, you "
                    "cannot provide an incompatible `sparse` argument."
                )
            batch_shape = input_tensor.shape
            dtype = input_tensor.dtype
            sparse = input_tensor.sparse
        else:
            if shape is not None and batch_shape is not None:
                raise ValueError(
                    "You cannot pass both `shape` and `batch_shape` at the "
                    "same time."
                )
            if batch_size is not None and batch_shape is not None:
                raise ValueError(
                    "You cannot pass both `batch_size` and `batch_shape` "
                    "at the same time."
                )
            if shape is None and batch_shape is None:
                raise ValueError("You must pass a `shape` argument.")

            if shape is not None:
                shape = backend.standardize_shape(shape)
                batch_shape = (batch_size,) + shape

        self._batch_shape = backend.standardize_shape(batch_shape)
        self._dtype = backend.standardize_dtype(dtype)
        self.sparse = bool(sparse)
        if self.sparse and not backend.SUPPORTS_SPARSE_TENSORS:
            raise ValueError(
                f"`sparse=True` is not supported with the {backend.backend()} "
                "backend"
            )
        self.ragged = bool(ragged)
        if self.ragged and not backend.SUPPORTS_RAGGED_TENSORS:
            raise ValueError(
                f"`ragged=True` is not supported with the {backend.backend()} "
                "backend"
            )

        if input_tensor is None:
            input_tensor = backend.KerasTensor(
                shape=batch_shape,
                dtype=dtype,
                sparse=sparse,
                ragged=ragged,
                name=name,
            )
        self._input_tensor = input_tensor
        Node(operation=self, call_args=(), call_kwargs={}, outputs=input_tensor)
        self.built = True
        self.optional = optional