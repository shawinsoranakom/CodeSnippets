def reduction_dtypes(
    arg,
    output_dtype_kind: REDUCTION_OUTPUT_TYPE_KIND,
    dtype: torch.dtype | None = None,
) -> tuple[torch.dtype, torch.dtype | None]:
    # even though some reductions, like amin or amax, don't strictly require type promotion,
    # all the math ops (including comparisons) are still defined only for a computation type,
    # so promotion will still happen. We are doing it explicitly here
    inp_dtype = dtype if dtype is not None else arg.dtype
    computation_dtype = get_computation_dtype(inp_dtype)
    if (
        output_dtype_kind == REDUCTION_OUTPUT_TYPE_KIND.SAME
        or output_dtype_kind == REDUCTION_OUTPUT_TYPE_KIND.COMPLEX_TO_FLOAT
    ):
        result_dtype = dtype if dtype else arg.dtype
        if (
            output_dtype_kind == REDUCTION_OUTPUT_TYPE_KIND.COMPLEX_TO_FLOAT
            and is_complex_dtype(result_dtype)
        ):
            result_dtype = corresponding_real_dtype(result_dtype)
    elif output_dtype_kind == REDUCTION_OUTPUT_TYPE_KIND.KEEP_PROMOTED_TYPE:
        result_dtype = None
    else:  # ALWAYS_BOOL
        result_dtype = torch.bool
    return computation_dtype, result_dtype