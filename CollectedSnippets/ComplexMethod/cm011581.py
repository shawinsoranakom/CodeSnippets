def floor_divide(a: TensorLikeType | NumberType, b: TensorLikeType | NumberType):
    # Wrap scalars because some references only accept tensor arguments.
    if isinstance(a, Number) and isinstance(b, Number):
        # pyrefly: ignore [bad-argument-type]
        a = scalar_tensor(a)
        # pyrefly: ignore [bad-argument-type]
        b = scalar_tensor(b)
    elif isinstance(b, Number) and isinstance(a, Tensor):
        # pyrefly: ignore [bad-argument-type]
        b = scalar_tensor(b, dtype=a.dtype, device=a.device)
    elif isinstance(a, Number) and isinstance(b, Tensor):
        # pyrefly: ignore [bad-argument-type]
        a = scalar_tensor(a, dtype=b.dtype, device=b.device)
    elif isinstance(a, Tensor) and isinstance(b, Tensor) and a.device != b.device:
        if a.device == torch.device("cpu"):
            msg = f"Expected divisor (b) to be on the same device ({a.device}) as dividend (a), but it is found on {b.device}!"
            raise RuntimeError(msg)
        else:
            b = prims.device_put(b, device=a.device)

    if not (isinstance(a, Tensor) and isinstance(b, Tensor)):
        raise AssertionError("a and b must both be Tensors at this point")
    dtype = a.dtype
    if utils.is_float_dtype(dtype):
        return _floor_divide_float(a, b)
    elif utils.is_integer_dtype(dtype):
        return _floor_divide_integer(a, b)
    else:
        torch._check(False, lambda: f"{dtype} not supported for floor_divide")