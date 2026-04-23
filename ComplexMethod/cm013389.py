def nep50_to_tensors(x1, x2, handle_weaks, function_name):
    """If either of inputs is a python scalar, type-promote with NEP 50."""

    def to_tensor(scalar, dtype=None):
        if dtype is None:
            dtype = _dtype_for_scalar(type(scalar))
            dtype = get_default_dtype_for(dtype)
        return torch.as_tensor(scalar, dtype=dtype)

    x1_is_weak = not isinstance(x1, torch.Tensor)
    x2_is_weak = not isinstance(x2, torch.Tensor)
    if not handle_weaks or (x1_is_weak and x2_is_weak):
        x1 = to_tensor(x1) if x1_is_weak else x1
        x2 = to_tensor(x2) if x2_is_weak else x2
        return x1, x2

    # scalar <op> tensor: NEP 50
    if x1_is_weak == x2_is_weak:
        raise AssertionError(
            f"Expected exactly one weak type, got x1_is_weak={x1_is_weak}, x2_is_weak={x2_is_weak}"
        )

    weak, not_weak = (x1, x2) if x1_is_weak else (x2, x1)

    # find the dtype for the weak's type
    weak_dtype = _dtype_for_scalar(type(weak))

    cat_weak = _category(weak_dtype)
    cat_not_weak = _category(not_weak.dtype)

    dt = not_weak.dtype if cat_weak <= cat_not_weak else None

    # special-case complex + float32
    if weak_dtype.is_complex and not_weak.dtype == torch.float32:
        dt = torch.complex64

    # detect overflows: in PyTorch, uint8(-1) wraps around to 255,
    # while NEP50 mandates an exception.
    #
    # Note that we only check if each element of the binop overflows,
    # not the result. Consider, e.g. `uint8(100) + 200`. Operands are OK
    # in uint8, but the result overflows and wrap around 255.
    # Numpy emits a RuntimeWarning, PyTorch does not, and we do not either.
    if cat_weak == 1 and cat_not_weak == 1:
        # integers
        iinfo = torch.iinfo(not_weak.dtype)
        if not (iinfo.min <= weak <= iinfo.max):
            raise OverflowError(
                f"Python integer {weak} out of bounds for {not_weak.dtype}"
            )
    if weak_dtype != dt or function_name in _NEP50_FUNCS_TENSOR_ONLY:
        # finally, can make `weak` into a 0D tensor, if both parameters are required to be tensor.
        weak = to_tensor(weak, dt)

    return (weak, not_weak) if x1_is_weak else (not_weak, weak)