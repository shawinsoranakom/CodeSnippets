def _check_valid_to_preserve(op_overload: "OperatorBase"):
    from torch._decomp import _should_decompose_because_unsafe_op

    if _should_decompose_because_unsafe_op(op_overload):
        return False
    if op_overload in FunctionalTensor.metadata_fns:
        return False

    if not hasattr(op_overload, "_schema"):
        return False

    alias_info = len(
        [i for i in op_overload._schema.arguments if i.alias_info is not None]
    )

    is_mutating_or_aliasing = alias_info != 0 or op_overload._schema.is_mutable

    if is_mutating_or_aliasing:
        return False

    if not torch._C._dispatch_has_kernel(op_overload.name()):
        return False

    return True