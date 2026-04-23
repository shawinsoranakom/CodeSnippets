def _register_post_backward_hook(
    state: _FSDPState,
    handle: FlatParamHandle | None,
) -> None:
    """
    Registers post-backward hooks on the ``FlatParameter`` s'
    ``AccumulateGrad`` objects to reshard and to reduce-scatter gradients.

    The ``AccumulateGrad`` object represents the last function that finalizes
    the ``FlatParameter`` 's gradient, so it only runs after its entire
    gradient computation has finished.

    We register the post-backward hook only once in the *first* forward that a
    ``FlatParameter`` participates in. This relies on the ``AccumulateGrad``
    object being preserved through multiple forwards.

    NOTE: We follow this heuristic to prefer the *first* forward to target the
    parameter mixed precision case, where there are *separate*
    ``AccumulateGrad`` objects across the different forwards. (Without
    parameter mixed precision, the ``AccumulateGrad`` objects are the same.) If
    we instead prefer the *last* forward, then the hook runs early.
    """
    # If there is no gradient computation, then there is no need for
    # post-backward logic
    if not torch.is_grad_enabled():
        return
    if not handle:
        return
    flat_param = handle.flat_param

    if torch.distributed._functional_collectives.is_torchdynamo_compiling():
        already_registered = hasattr(flat_param, "_post_backward_hook_handle")
        if already_registered or not flat_param.requires_grad:
            return
        hook = functools.partial(_post_backward_hook, state, handle)
        hook_handle = flat_param.register_post_accumulate_grad_hook(hook)
        flat_param._post_backward_hook_handle = hook_handle  # type: ignore[attr-defined]
    else:
        already_registered = hasattr(flat_param, "_post_backward_hook_state")
        if already_registered or not flat_param.requires_grad:
            return
        # Get the `AccumulateGrad` object
        temp_flat_param = flat_param.expand_as(flat_param)
        _p_assert(
            temp_flat_param.grad_fn is not None,
            "The `grad_fn` is needed to access the `AccumulateGrad` and "
            "register the post-backward hook",
        )
        acc_grad = temp_flat_param.grad_fn.next_functions[0][0]  # type: ignore[union-attr]
        if acc_grad is None:
            raise AssertionError("Expected acc_grad to be set")
        hook_handle = acc_grad.register_hook(
            functools.partial(_post_backward_hook, state, handle)
        )
        flat_param._post_backward_hook_state = (acc_grad, hook_handle)