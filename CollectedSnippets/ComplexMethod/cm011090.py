def _register_post_backward_reshard_only_hook(
    state: _FSDPState,
    handle: FlatParamHandle | None,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> None:
    """
    Registers post-backward hooks to reshard flat parameters that do not
    require gradient. We register these using multi-post-grad hooks on the
    input activations to ensure that all gradients that may depend on the
    parameters have been computed before resharding.
    """
    # If there is no gradient computation, then there is no need for
    # post-backward logic
    if not torch.is_grad_enabled():
        return
    # Construct `inp_tensors` lazily to avoid CPU overhead in typical case
    # where each flat parameter requires gradient
    inp_tensors: list[torch.Tensor] | None = None
    if not handle:
        return
    flat_param = handle.flat_param

    if torch.distributed._functional_collectives.is_torchdynamo_compiling():
        already_registered = hasattr(flat_param, "_post_backward_hook_handle")
    else:
        already_registered = hasattr(flat_param, "_post_backward_hook_state")

    if already_registered or flat_param.requires_grad:
        return
    if inp_tensors is None:
        args_flat = pytree.arg_tree_leaves(*args, **kwargs)
        inp_tensors = [
            obj for obj in args_flat if torch.is_tensor(obj) and obj.requires_grad
        ]
    if inp_tensors is None:
        raise AssertionError("Expected inp_tensors to be set")
    hook_handle = register_multi_grad_hook(
        inp_tensors, functools.partial(_post_backward_reshard_only_hook, state, handle)
    )
    if torch.distributed._functional_collectives.is_torchdynamo_compiling():
        flat_param._post_backward_hook_handle = hook_handle  # type: ignore[attr-defined, assignment]
    else:
        flat_param._post_backward_hook_state = (hook_handle,)