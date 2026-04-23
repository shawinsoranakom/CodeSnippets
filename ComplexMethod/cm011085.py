def _post_backward_hook(
    state: _FSDPState,
    handle: FlatParamHandle,
    flat_param,
    *unused: Any,
):
    """
    Reduce-scatters the gradient of ``handle`` 's ``FlatParameter``.

    Precondition: The ``FlatParameter`` 's ``.grad`` attribute contains the
    unsharded gradient for the local batch.

    Postcondition:
    - If using ``NO_SHARD``, then the ``.grad`` attribute is the reduced
    unsharded gradient.
    - Otherwise, the ``_saved_grad_shard`` attribute is the reduced sharded
    gradient (accumulating with any existing gradient).
    """
    _log_post_backward_hook(state, handle, logger)
    flat_param = handle.flat_param
    flat_param._post_backward_called = True
    with torch.autograd.profiler.record_function(
        "FullyShardedDataParallel._post_backward_hook"
    ):
        _assert_in_training_states(state, [TrainingState.FORWARD_BACKWARD])
        # For multiple applications of reentrant AC across submodules sharing
        # the same `FlatParameter`, the post-backward hook may run multiple
        # times in one backward, in which case we permit the state to already
        # be in `BACKWARD_POST`.
        _p_assert(
            handle._training_state
            in (HandleTrainingState.BACKWARD_PRE, HandleTrainingState.BACKWARD_POST),
            f"Expects `BACKWARD_PRE` or `BACKWARD_POST` state but got {handle._training_state}",
        )
        handle._training_state = HandleTrainingState.BACKWARD_POST

        if flat_param.grad is None:
            return
        if flat_param.grad.requires_grad:
            raise RuntimeError("FSDP does not support gradients of gradients")

        _post_backward_reshard(state, handle)
        if not state._sync_gradients:
            if handle._use_orig_params:
                handle._use_unsharded_grad_views()
            return

        # Wait for all ops in the current stream (e.g. gradient computation) to
        # finish before reduce-scattering the gradient
        if not torch.distributed._functional_collectives.is_torchdynamo_compiling():
            state._post_backward_stream.wait_stream(
                state._device_handle.current_stream()
            )

        with state._device_handle.stream(state._post_backward_stream):
            autograd_computed_grad = flat_param.grad.data
            if (
                not _low_precision_hook_enabled(state)
                and flat_param.grad.dtype != handle._reduce_dtype
                # If we are forcing full precision but communicating grads
                # (i.e. model.eval() + full precision in eval was configured), don't downcast gradient.
                and not handle._force_full_precision
            ):
                flat_param.grad.data = flat_param.grad.to(handle._reduce_dtype)
            if handle.uses_sharded_strategy:
                _reduce_grad(state, handle)
            else:
                _reduce_grad_no_shard(state, handle)
            # Since the unsharded gradient is produced in the computation
            # stream and consumed in the post-backward stream, inform the
            # caching allocator (before it goes out of scope)
            _no_dispatch_record_stream(
                autograd_computed_grad, state._post_backward_stream
            )