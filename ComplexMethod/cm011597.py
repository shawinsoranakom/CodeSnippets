def _reshape_view_helper(a: TensorLikeType, *shape, allow_copy: bool) -> TensorLikeType:
    # Creates a valid shape
    shape = utils.extract_shape_from_varargs(shape, validate=False)
    # Reshape may be given a shape with a -1 length
    # This indicates that the dimension's length should be inferred
    shape = utils.infer_size(shape, a.numel())

    # Special-cases tensors with no elements
    if a.numel() == 0:
        return as_strided(a, shape, utils.make_contiguous_strides_for(shape))

    # Special-cases reshaping zero dim tensors
    if a.ndim == 0:
        _a = a
        for length in shape:
            if length != 1:
                raise AssertionError(
                    f"Cannot reshape 0-dim tensor: shape dimension must be 1, got {length}"
                )
            _a = unsqueeze(_a, -1)
        if _a is a:
            return prims.view_of(a)
        else:
            return _a

    # Special-cases reshaping to zero dim tensors
    if len(shape) == 0:
        _a = a
        for length in a.shape:
            if length != 1:
                raise AssertionError(
                    f"Cannot reshape to 0-dim tensor: shape dimension must be 1, got {length}"
                )
            _a = squeeze(_a, -1)
        if _a is a:
            return prims.view_of(a)
        else:
            return _a

    if is_contiguous_or_false(a):
        # Special-cases for nd_to_1d
        if len(shape) == 1 and a.ndim > 1:
            return torch.as_strided(a, [a.numel()], [1])
        # Special-cases for 1d_to_2d
        if len(shape) == 2 and a.ndim == 1:
            dim0 = shape[0]
            dim1 = shape[1]
            return torch.as_strided(a, [dim0, dim1], [dim1, 1])

    shape_numel = reduce(operator.mul, shape, 1)
    torch._check(
        a.numel() == shape_numel,
        lambda: f"Could not reshape a tensor with shape {a.shape} as a tensor with shape {shape}!",
    )

    # Handles general case: a 1+D tensor reshaped into a distinct 1+D shape
    return _reshape_view_helper_core_alg(a, shape, allow_copy)