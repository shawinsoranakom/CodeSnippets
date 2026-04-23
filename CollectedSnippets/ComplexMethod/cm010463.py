def _can_decompose_fast(
    func: OpOverload, export: bool, pre_dispatch: bool
) -> bool | None:
    """Fast path for _can_decompose that depends only on (func, export, pre_dispatch).

    Returns True/False for a definitive answer, or None to fall through
    to the slow path (autograd_would_have_decomposed).
    """
    if export and func is torch.ops.aten.dropout.default:
        return False

    from torch._decomp import _should_decompose_because_unsafe_op

    if _should_decompose_because_unsafe_op(func):
        return True

    alias_info_present = any(arg.alias_info for arg in func._schema.arguments)
    if alias_info_present or func._schema.is_mutable:
        return True

    if export:
        if pre_dispatch:
            if func.namespace not in ("aten", "prim") and func._can_decompose():
                warnings.warn(
                    f"At pre-dispatch tracing, we assume that any custom op marked with "
                    f"CompositeImplicitAutograd and have functional schema are safe to not decompose. "
                    f"Found {func} to be one such op.",
                    stacklevel=3,
                )
            return False
        return True

    return None