def _finalize_params(
    state: _FSDPState,
) -> None:
    """Finalizes the parameters before the next iteration."""
    handle = state._handle
    if not handle:
        return
    flat_param = handle.flat_param
    if torch.distributed._functional_collectives.is_torchdynamo_compiling():
        if hasattr(flat_param, "_post_backward_hook_handle"):
            pbhs_handle = flat_param._post_backward_hook_handle
            pbhs_handle.remove()
            del flat_param._post_backward_hook_handle
    else:
        if hasattr(flat_param, "_post_backward_hook_state"):
            post_backward_hook_state_len = len(flat_param._post_backward_hook_state)
            expected_post_backward_hook_state_len = int(flat_param.requires_grad) + 1
            _p_assert(
                post_backward_hook_state_len == expected_post_backward_hook_state_len,
                f"Invalid: ``_post_backward_hook_state``: {flat_param._post_backward_hook_state}",
            )
            flat_param._post_backward_hook_state[-1].remove()
            delattr(flat_param, "_post_backward_hook_state")
    if flat_param.requires_grad:
        if not state._sync_gradients:
            # Preserve the gradient accumulation state if not synchronizing
            # gradients: `.grad` remains the unsharded gradient  from prior
            # `no_sync()` iterations, and `_saved_grad_shard` remains the
            # sharded gradient from the last synchronized iteration
            return
        if not handle._has_optim_in_backward:
            handle.prepare_gradient_for_optim()
        _p_assert(
            hasattr(flat_param, "_post_backward_called"),
            "Expects `_post_backward_called` to be set on the `FlatParameter`",
        )
        flat_param._post_backward_called = False