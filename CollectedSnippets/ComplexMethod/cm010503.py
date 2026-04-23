def _grad_context_compatible(
    symbolic_context: torch.fx.experimental.symbolic_shapes.SymbolicContext,
    grad_desc: MetaTensorDesc[torch.Tensor],
) -> bool:
    """Check if a symbolic_context is compatible with a grad tensor.

    Returns False when the view base structure in symbolic_context doesn't
    match the grad, which means we need a fresh symbolic context.  This
    happens in FSDP2 where param._local_tensor is a view of an N-D padded
    base while grad._local_tensor is a view of a 1-D flat gradient buffer.

    We check at both the outer level and the inner (subclass attr) level.
    """
    from torch.fx.experimental.symbolic_shapes import (
        StatelessSymbolicContext,
        SubclassSymbolicContext,
    )

    def _view_base_compatible(
        ctx: StatelessSymbolicContext[Any, Any],
        grad_t: MetaTensorDesc[torch.Tensor],
    ) -> bool:
        vbc = ctx.view_base_context
        if grad_t.is_view and vbc is None:
            return False
        if not grad_t.is_view and vbc is not None:
            return False
        if (
            grad_t.is_view
            and vbc is not None
            and isinstance(vbc, StatelessSymbolicContext)
            and grad_t.base is not None
            and len(vbc.dynamic_sizes) != grad_t.base.ndim
        ):
            return False
        return True

    if not isinstance(symbolic_context, StatelessSymbolicContext):
        return True

    # Check outer level
    if not _view_base_compatible(symbolic_context, grad_desc):
        return False

    # Check inner (subclass) level
    if isinstance(symbolic_context, SubclassSymbolicContext):
        if grad_desc.attrs is None:
            return False
        for attr, inner_ctx in symbolic_context.inner_contexts.items():
            if attr not in grad_desc.attrs:
                return False
            if isinstance(
                inner_ctx, StatelessSymbolicContext
            ) and not _view_base_compatible(inner_ctx, grad_desc.attrs[attr]):
                return False

    return True