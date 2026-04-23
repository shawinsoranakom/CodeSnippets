def get_higher_dtype(
    a: torch.dtype | TensorLikeType | NumberType | None,
    b: torch.dtype | TensorLikeType | NumberType | None,
) -> torch.dtype | None:
    """
    Computes the "lowest" datatype that is weakly
    "higher" than both a and b.
    """

    # Type checking
    if a is not None and not isinstance(a, (torch.dtype, TensorLike, Number)):
        raise AssertionError(
            f"a must be None, torch.dtype, TensorLike, or Number, got {type(a)}"
        )
    if b is not None and not isinstance(b, (torch.dtype, TensorLike, Number)):
        raise AssertionError(
            f"b must be None, torch.dtype, TensorLike, or Number, got {type(b)}"
        )

    def _extract_dtype(
        x: torch.dtype | TensorLikeType | NumberType | None,
    ) -> torch.dtype | None:
        if x is None:
            return None
        if isinstance(x, torch.dtype):
            return x
        if isinstance(x, TensorLike):
            return x.dtype
        if isinstance(x, Number):
            return type_to_dtype(type(x))

        raise RuntimeError("Unexpected type given to _extract_dtype!")

    a, b = _extract_dtype(a), _extract_dtype(b)

    if a is b:
        return a

    if a is None:
        return b

    if b is None:
        return a

    ordered_datatypes = (
        (torch.bool,),
        (torch.uint8, torch.int8),
        (torch.int16,),
        (torch.int32,),
        (torch.int64,),
        (torch.float16, torch.bfloat16),
        (torch.float32,),
        (torch.float64,),
        (torch.complex32,),
        (torch.complex64,),
        (torch.complex128,),
    )

    for idx, dtypes in enumerate(ordered_datatypes):
        if a in dtypes and b in dtypes:
            return ordered_datatypes[idx + 1][0]
        if a in dtypes:
            return b
        if b in dtypes:
            return a

    raise RuntimeError("Unexpected termination!")