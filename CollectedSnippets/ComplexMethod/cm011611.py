def _canonicalize_fft_shape_and_dim_args(
    input: TensorLikeType, shape: ShapeType | None, dim: DimsType | None
) -> _ShapeAndDims:
    """Convert the shape and dim arguments into a canonical form where neither are optional"""
    input_dim = input.ndim
    input_sizes = input.shape

    if dim is not None:
        if not isinstance(dim, Sequence):
            dim = (dim,)
        ret_dims = utils.canonicalize_dims(input_dim, dim, wrap_scalar=False)

        # Check dims are unique
        torch._check(
            len(set(ret_dims)) == len(ret_dims), lambda: "FFT dims must be unique"
        )

    if shape is not None:
        if not isinstance(shape, Sequence):
            shape = (shape,)

        # Has shape, might have dim
        torch._check(
            dim is None or len(dim) == len(shape),
            lambda: "When given, dim and shape arguments must have the same length",
        )
        transform_ndim = len(shape)

        torch._check(
            transform_ndim <= input_dim,
            lambda: f"Got shape with {transform_ndim} values but input tensor "
            f"only has {input_dim} dimensions.",
        )

        # If shape is given, dims defaults to the last len(shape) dimensions
        if dim is None:
            ret_dims = tuple(range(input_dim - transform_ndim, input_dim))

        # Translate any -1 values in shape to the default length
        ret_shape = tuple(
            s if s != -1 else input_sizes[d]
            for (s, d) in zip(shape, ret_dims)  # type: ignore[possibly-undefined]
        )
    elif dim is None:
        # No shape, no dim
        ret_dims = tuple(range(input_dim))
        ret_shape = tuple(input_sizes)
    else:
        # No shape, has dim
        ret_shape = tuple(input_sizes[d] for d in ret_dims)  # type: ignore[possibly-undefined]

    for n in ret_shape:
        torch._check(n > 0, lambda: f"Invalid number of data points ({n}) specified")

    return _ShapeAndDims(shape=ret_shape, dims=ret_dims)