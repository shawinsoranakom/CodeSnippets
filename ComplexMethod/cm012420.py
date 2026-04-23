def reduction_init(reduction_type, dtype):
    if dtype in DTYPE_LOWP_FP:
        # Since load promotes all half-precision inputs to float, the initial
        # constant for reduction must be promoted as well
        dtype = torch.float32
    if reduction_type in ("xor_sum", "sum", "any"):
        return 0
    if reduction_type == "prod":
        return 1
    if reduction_type in ("max", "argmax", "min", "argmin"):
        cdtype = DTYPE_TO_CPP[dtype]
        if dtype == torch.bool and reduction_type in ("argmin", "argmax"):
            cdtype = DTYPE_TO_CPP[torch.float]
        min_var = (
            f"-std::numeric_limits<{cdtype}>::infinity()"
            if is_float_dtype(dtype)
            else f"std::numeric_limits<{cdtype}>::min()"
        )
        max_var = (
            f"std::numeric_limits<{cdtype}>::infinity()"
            if is_float_dtype(dtype)
            else f"std::numeric_limits<{cdtype}>::max()"
        )
        init_var = min_var if reduction_type in ("max", "argmax") else max_var
        return (
            init_var
            if reduction_type in ("max", "min")
            else f"IndexValue<{cdtype}>{{0, {init_var}}}"
        )
    if is_welford_reduction(reduction_type):
        return f"Welford<{DTYPE_TO_CPP[dtype]}>()"
    raise AssertionError(reduction_type)