def matmul(x1, x2):
    x1 = convert_to_tensor(x1)
    x2 = convert_to_tensor(x2)
    x1_dtype = standardize_dtype(x1.dtype)
    x2_dtype = standardize_dtype(x2.dtype)

    def can_use_int_matmul(x1, x2):
        # torch._int_mm only accepts the following conditions:
        # 1. cuda
        # 2. both inputs must have int8 dtype
        # 3. both inputs must be 2d
        # 4. x1.shape must be [>16, >= 16 and a multiplier of 8]
        # 5. x2.shape must be [>= 16 and a multiplier of 8, multiplier of 8]
        if get_device() != "cuda":
            return False
        if x1_dtype != "int8" or x2_dtype != "int8":
            return False
        x1_shape = x1.shape
        x2_shape = x2.shape
        if x1.ndim != 2 or x2.ndim != 2:
            return False
        if x1_shape[0] <= 16 or x1_shape[1] < 16 or x1_shape[1] % 8 != 0:
            return False
        if x2_shape[0] < 16 or x2_shape[0] % 8 != 0 or x2_shape[1] % 8 != 0:
            return False
        return True

    # Shortcut for torch._int_mm
    # TODO: Loosen the restriction of the usage of torch._int_mm
    # TODO: We should replace torch._int_mm with the public api if possible
    # Not yet supported with CUDA 13 without `use_transpose`
    # https://github.com/pytorch/pytorch/blob/main/test/test_linalg.py#L7876
    if can_use_int_matmul(x1, x2):
        try:
            return torch._int_mm(x1, x2)
        except RuntimeError:
            pass

    if x1_dtype == "int8" and x2_dtype == "int8":
        result_dtype = "int32"
    else:
        result_dtype = dtypes.result_type(x1.dtype, x2.dtype)
    compute_dtype = result_dtype

    # TODO: torch.matmul doesn't support bool
    if compute_dtype == "bool":
        compute_dtype = config.floatx()
    # TODO: torch.matmul doesn't support float16 with cpu
    if get_device() == "cpu" and compute_dtype == "float16":
        compute_dtype = "float32"
    # TODO: torch.matmul doesn't support integer types with cuda
    if get_device() == "cuda" and "int" in compute_dtype:
        compute_dtype = config.floatx()

    x1 = cast(x1, compute_dtype)
    x2 = cast(x2, compute_dtype)
    return cast(torch.matmul(x1, x2), result_dtype)