def check_autodiff_sample(op, sample, dtype, is_inplace):
    if op.name == "_foreach_abs" and is_inplace and dtype == torch.complex128:
        return False, "In-place abs is not supported for complex tensors."
    if op.name == "_foreach_sub" and (
        (
            isinstance(sample.args[-1], list)
            and any(isinstance(a, bool) for a in sample.args[-1])
        )
        or isinstance(sample.args[-1], bool)
    ):
        return False, _BOOL_SUB_ERR_MSG
    if op.name == "_foreach_norm" and (not is_inplace):
        return (
            False,
            "Trying to set a forward gradient that has a different size than that of the original Tensor, "
            "this is not supported. Tensor is of size [] while the given forward gradient is of size [1",
        )
    rhs_arg_has_complex_number = sample.args and (
        (
            isinstance(sample.args[-1], list)
            and any(isinstance(a, complex) for a in sample.args[-1])
        )
        or (isinstance(sample.args[-1], complex))
    )
    if rhs_arg_has_complex_number and dtype == torch.float64:
        if op.name == "_foreach_lerp":
            return False, "value cannot be converted to type double without overflow"
        if op.name in (
            "_foreach_clamp_max",
            "_foreach_clamp_min",
            "_foreach_maximum",
            "_foreach_minimum",
        ):
            return False, "clamp is not supported for complex types"
        if op.name == "_foreach_lerp" and is_inplace:
            return False, "value cannot be converted to type double without overflow"
        if not is_inplace:
            return False, ""
        elif op.name in (
            "_foreach_add",
            "_foreach_sub",
            "_foreach_mul",
            "_foreach_div",
            "_foreach_pow",
        ):
            return (
                False,
                "result type ComplexDouble can't be cast to the desired output type Double",
            )
    return True, ""