def _pre_forward(
    state: _FSDPState,
    handle: FlatParamHandle | None,
    unshard_fn: Callable,
    module: nn.Module,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[tuple[Any, ...], dict[str, Any]]:
    """
    Runs the pre-forward logic. This includes an opportunity to unshard
    currently sharded parameters such as those for the current forward and
    registering post-backward hooks for these current parameters. This function
    also converts forward ``args`` and ``kwargs`` to the given precision.

    Args:
        handles (List[FlatParamHandle]): Handles giving the parameters used in
            the current forward.
        unshard_fn (Optional[Callable]): A callable to unshard any currently
            sharded parameters or ``None`` to not do any unsharding.
        module (nn.Module): Module whose forward this method runs right before;
            expected by the hook signature.
        args (Tuple[Any, ...]): Module forward ``args``.
        kwargs (Dict[str, Any]): Module forward ``kwargs``.
    """
    with torch.profiler.record_function("FullyShardedDataParallel._pre_forward"):
        # For `fully_shard` + `checkpoint`, skip pre-forward logic in the
        # recomputed forward
        if handle and handle._training_state == HandleTrainingState.BACKWARD_PRE:
            # For both checkpoint implementations, we do not need to re-cast
            # inputs here since they will be checkpointed in the low precision
            # either by AC or normally by autograd as long as the AC region is
            # nested within FSDP
            return args, kwargs
        state.training_state = TrainingState.FORWARD_BACKWARD
        state._exec_order_data.record_pre_forward(handle, module.training)
        if handle:
            handle._training_state = HandleTrainingState.FORWARD
        if unshard_fn is not None:
            unshard_fn(state, handle)
        # Register post-backward hooks to reshard the parameters and reduce-scatter
        # their gradients. They must be re-registered every forward pass in case
        # the `grad_fn` is mutated.
        _register_post_backward_hook(state, handle)
        # We have to reallocate the _cpu_grad if optimizer overlap
        # set the grad to None in the backward pass.
        if handle and handle._offload_params and handle.flat_param._cpu_grad is None:
            handle.flat_param._cpu_grad = torch.zeros_like(
                handle.flat_param._local_shard, device=torch.device("cpu")
            ).pin_memory()

        should_cast_forward_inputs = (
            state._handle and not state._handle._force_full_precision
        )

        if should_cast_forward_inputs and state.mixed_precision.cast_forward_inputs:
            # Recursively convert args and kwargs to specified precision.
            input_dtype: torch.dtype | None = state.mixed_precision.param_dtype
            args, kwargs = _cast_forward_inputs(input_dtype, *args, **kwargs)
        _register_post_backward_reshard_only_hook(state, handle, args, kwargs)
        return args, kwargs