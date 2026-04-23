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