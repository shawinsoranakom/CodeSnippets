def _prim_elementwise_meta(
    *args,
    type_promotion: ELEMENTWISE_PRIM_TYPE_PROMOTION_KIND,
    args_with_fixed_dtypes: tuple[TensorLikeType, ...] | None = None,
) -> FakeTensor:
    """
    Meta function for elementwise operations that produce outputs in the same dtype
    as their inputs.

    Stride logic is currently incorrect.
    """

    if len(args) == 0:
        raise AssertionError("elementwise operation requires at least one argument")

    utils.check_same_dtype(*args)

    args_ = list(args)
    if args_with_fixed_dtypes is not None:
        args_ = list(args_with_fixed_dtypes) + args_

    utils.check_same_device(*args_, allow_cpu_scalar_tensors=True)
    utils.check_same_shape(*args_, allow_cpu_scalar_tensors=True)

    l2p_perm, _ = utils.compute_elementwise_output_logical_to_physical_perm(*args_)
    shape = utils.extract_shape(*args_, allow_cpu_scalar_tensors=True)

    # Acquires the dtype
    dtype = None
    scalar_type = None
    for arg in args:
        if isinstance(arg, TensorLike):
            if not utils.is_cpu_scalar_tensor(arg):
                dtype = arg.dtype
                break
            else:
                dtype = arg.dtype
        elif isinstance(arg, Number):
            scalar_type = type(arg)

    if dtype is None and scalar_type is not None:
        dtype = utils.type_to_dtype(scalar_type)

    # Acquires the device (if it exists) or number
    device = None
    number = None
    # pyrefly: ignore [bad-assignment]
    for arg in args_:
        if isinstance(arg, TensorLike):
            if utils.is_cpu_scalar_tensor(arg):
                if device is None:
                    device = arg.device
                # keep going, in case there is a cuda tensor later
            else:
                device = arg.device
                break

        elif isinstance(arg, Number):
            if number is None:
                number = arg

    # NOTE: type promotion behavior here is mostly hidden from tests because
    # references will typically handle the type promotion properly even if this doesn't
    # (but getting it wrong will cause too many casts to be inserted in traces!)
    if device is not None:
        if dtype is None:
            raise AssertionError("dtype must not be None when device is not None")
        if type_promotion == ELEMENTWISE_PRIM_TYPE_PROMOTION_KIND.ALWAYS_BOOL:
            dtype = torch.bool
        elif type_promotion == ELEMENTWISE_PRIM_TYPE_PROMOTION_KIND.INT_TO_FLOAT:
            if utils.is_integer_dtype(dtype) or utils.is_boolean_dtype(dtype):
                dtype = torch.get_default_dtype()
        elif type_promotion == ELEMENTWISE_PRIM_TYPE_PROMOTION_KIND.COMPLEX_TO_FLOAT:
            if utils.is_complex_dtype(dtype):
                dtype = utils.corresponding_real_dtype(dtype)

        if shape is None:
            raise AssertionError("shape must not be None when device is not None")
        return torch.empty_permuted(shape, l2p_perm, device=device, dtype=dtype)  # type: ignore[return-value]

    # Number case
    # TODO: fix number type promotion (bool, complex->float)

    # For now for symint/float, just implementing the common / simple cases of (int,float,symint,symfloat)
    seen_float = False
    if isinstance(number, (torch.SymInt, torch.SymFloat)):
        for a in args:
            if not isinstance(a, (int, float, torch.SymInt, torch.SymFloat)):
                raise AssertionError(
                    f"Expected int, float, SymInt, or SymFloat, got {type(a)}"
                )
            seen_float = seen_float or isinstance(a, (float, torch.SymFloat))
        if seen_float:
            number = sym_float(number)

    return TensorMeta(number)