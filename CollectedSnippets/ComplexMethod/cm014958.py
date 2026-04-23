def should_check_strides(func):
    if func in CHECK_ALL_STRIDES:
        return CheckStrides.ALL
    if func in CHECK_STRIDES:
        return CheckStrides.SIGNIFICANT
    if func in CHECK_STRIDES_SKIPS:
        return CheckStrides.NONE
    if not isinstance(func, torch._ops.OpOverload):
        return CheckStrides.NONE
    # Prims are expected to model strides correctly
    if func.namespace == "prims":
        return CheckStrides.SIGNIFICANT
    # Check if it's a view, by testing if any of the returns have
    # a non-empty alias set
    if any(r.alias_info.before_set for r in func._schema.returns if r.alias_info):
        return CheckStrides.SIGNIFICANT
    # TODO: check for TensorIterator
    return CheckStrides.SIGNIFICANT