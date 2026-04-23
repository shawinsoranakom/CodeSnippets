def _pre_backward_hook(
    state: _FSDPState,
    module: nn.Module,
    handle: FlatParamHandle,
    grad,
    *unused: Any,
) -> Any:
    """
    Prepares ``_handle`` 's ``FlatParameter`` s for gradient computation.

    Args:
        module (nn.Module): Fully sharded module (see [Note: Fully Sharded
            Module]).
    """
    # Only run the pre-backward hook once per group of handles involved in the
    # same module forward computation
    if (
        handle
        and hasattr(handle, "_ran_pre_backward_hook")
        and handle._ran_pre_backward_hook
    ):
        return grad

    with torch.profiler.record_function("FullyShardedDataParallel._pre_backward_hook"):
        # Queue the post-backward callback once for the root FSDP instance to
        # attach it to the outermost backward graph task so that it is called
        # after all backward calls complete
        if state._is_root and not state._post_backward_callback_queued:
            _register_post_backward_final_callback(state, module)
            _reset_flat_param_grad_info_if_needed(state._all_handles)
        elif handle:
            allowed_states = [TrainingState.IDLE]
            if _is_composable(state):
                allowed_states.append(TrainingState.FORWARD_BACKWARD)
            _assert_in_training_states(state, allowed_states)
        state.training_state = TrainingState.FORWARD_BACKWARD
        # Queueing the post-backward callback is the only logic that is not
        # per-handle in the pre-backward hook, so we can return early here if
        # there are no handles.
        if not handle:
            return grad
        handle._training_state = HandleTrainingState.BACKWARD_PRE

        if handle._needs_pre_backward_unshard:
            # If the handles have been prefetched, then there is no need to
            # call `_unshard()` again
            if not handle._prefetched:
                _unshard(
                    state,
                    handle,
                    state._unshard_stream,
                    state._pre_unshard_stream,
                )
            # Don't wait during trace
            if not torch.distributed._functional_collectives.is_torchdynamo_compiling():
                state._device_handle.current_stream().wait_stream(state._unshard_stream)

        # Set this to `False` to ensure that a mistargeted prefetch does not
        # actually unshard these handles
        handle._needs_pre_backward_unshard = False
        with torch.profiler.record_function(
            "FullyShardedDataParallel._pre_backward_prefetch"
        ):
            _prefetch_handle(state, handle, _PrefetchMode.BACKWARD)
        handle.prepare_gradient_for_backward()
        handle._ran_pre_backward_hook = True
        return grad