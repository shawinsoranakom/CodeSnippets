def _unshard_fsdp_state_params(
    module: nn.Module,
    state: _FSDPState,
    writeback: bool,
    rank0_only: bool,
    offload_to_cpu: bool,
    with_grads: bool,
):
    """
    This unshards the parameters for a single FSDP state ``state`` that
    corresponds to ``module``.
    """
    _validate_unshard_params_args(
        state, writeback, rank0_only, offload_to_cpu, with_grads
    )
    state._device_handle.synchronize()
    # If handles are shared by other module(s), the handle may be already unsharded.
    maybe_handle = _module_handle(state, module)
    handle = None
    if (
        maybe_handle
        and maybe_handle._training_state != HandleTrainingState.SUMMON_FULL_PARAMS
    ):
        handle = maybe_handle
    if not handle:
        yield
        return

    if handle._training_state != HandleTrainingState.IDLE:
        raise AssertionError(
            f"Expects the handle training to be IDLE but got {handle._training_state}"
        )

    handle._training_state = HandleTrainingState.SUMMON_FULL_PARAMS

    _reset_flat_param_grad_info_if_needed(handle)
    free_unsharded_flat_param = handle.needs_unshard()
    # No need to call `wait_stream()` since we unshard in the computation
    # stream directly
    computation_stream = state._device_handle.current_stream()
    _unshard(state, handle, computation_stream, computation_stream)
    if with_grads:
        _unshard_grads(handle)

    if rank0_only and state.rank != 0:
        # Free the unsharded flattened parameter early
        _reshard(state, handle, free_unsharded_flat_param)
        if with_grads:
            _reshard_grads(handle)
        try:
            yield
        finally:
            handle._training_state = HandleTrainingState.IDLE
    else:
        # Unflatten the unsharded flattened parameters
        with contextlib.ExitStack() as stack:
            # Invariant: rank == 0 or !rank0_only
            if offload_to_cpu and handle.uses_sharded_strategy:
                stack.enter_context(handle.to_cpu())
                # NOTE: Since PyTorch enforces that a parameter and its
                # gradients need to match metadata (e.g. device), we must
                # move gradients to CPU *after* we move parameters.
            # NOTE: This assumes 1 `FlatParameter`
            if not state._use_orig_params:
                stack.enter_context(_unflatten_as_params(state, module))
            try:
                yield
            finally:
                stack.close()
                if writeback:
                    _writeback_to_local_shard(handle, with_grads)
                _reshard(state, handle, free_unsharded_flat_param)
                if with_grads:
                    _reshard_grads(handle)
                handle._training_state = HandleTrainingState.IDLE