def _root_pre_forward(
    state: _FSDPState,
    module: nn.Module,
    args,
    kwargs,
) -> None:
    """
    Runs pre-forward logic specific to the root FSDP instance, which should run
    before any individual module's pre-forward. This starts with an attempt at
    lazy initialization (which only runs non-vacuously once). Otherwise, if
    this is called on a non-root FSDP instance, then it returns directly.

    Args:
        module (nn.Module): Module for which this logic tries to run. It may or
            may not be the root. If not, then this method does not do anything.
    """
    with torch.profiler.record_function("FullyShardedDataParallel._root_pre_forward"):
        _lazy_init(state, module)
        _p_assert(state._is_root is not None, "Expects a root FSDP to have been set")
        if not state._is_root:
            # Always cast forward inputs in the root of this local FSDP unit for mixed
            # precision, as this is where mixed precision could be configured.
            # This is more useful for auto wrapping that is recommended in composable path.
            # For manual wrapping, cast forward inputs on each local FSDP unit root will
            # increase some overhead, so not turned on for model wrapper path right now where
            # manual wrapping is more broadly used.
            if _is_composable(state):
                return _root_cast_forward_input(state, module, args, kwargs)
            return args, kwargs

        # We cast buffers back to full precision if we're forcing full precision. Disjointly, we check if buffers
        # are in full precision and if we should cast them back to lower precision, which happens when
        # exiting eval() mode.
        handle = state._handle
        if handle:
            should_cast_buffers_to_full_prec = handle._force_full_precision
        else:
            # If the root has no handle (no managed parameters), then we fall
            # back to checking if any child wants to force full precision as a
            # workaround
            handles = traversal_utils._get_fsdp_handles(module)
            should_cast_buffers_to_full_prec = any(
                handle._force_full_precision for handle in handles
            )

        if should_cast_buffers_to_full_prec:
            _cast_buffers_to_dtype_and_device(
                buffers=dict(module.named_buffers()).values(),
                buffer_dtypes=list(state._buffer_name_to_orig_dtype.values()),
                device=state.compute_device,
            )
            # This flag is only set when we cast buffers to full precision, to avoid the
            # CPU overhead that can stem from retrieving all buffers and their types in the
            # following else branch.
            state._needs_buffer_dtype_restore_check = True
        elif getattr(state, "_needs_buffer_dtype_restore_check", False):
            # Check if buffers are in full precision and we need to cast them
            # back down.
            (
                buffers,
                buffer_dtypes_for_computation,
            ) = _get_buffers_and_dtypes_for_computation(state, module)
            if len(buffers) > 0 and len(buffer_dtypes_for_computation) > 0:
                if any(
                    buffer.dtype != buffer_dtype_for_computation
                    for buffer, buffer_dtype_for_computation in zip(
                        buffers, buffer_dtypes_for_computation
                    )
                ):
                    # Assume we have to cast everything if there is one mismatch
                    _cast_buffers_to_dtype_and_device(
                        buffers, buffer_dtypes_for_computation, state.compute_device
                    )
            # We don't have to check this again until we cast buffers to full precision again.
            state._needs_buffer_dtype_restore_check = False

        if state.forward_prefetch:
            handles = [
                fsdp_state._handle
                for fsdp_state in state._all_fsdp_states
                if fsdp_state._handle
            ]
            for handle in handles:
                handle._needs_pre_forward_unshard = True
                handle._prefetched = False
        _wait_for_computation_stream(
            state._device_handle.current_stream(),
            state._unshard_stream,
            state._pre_unshard_stream,
        )
        _reset_flat_param_grad_info_if_needed(state._all_handles)

        # Prepares the forward inputs by moving them to ``compute_device``
        # TODO: Do not use the side stream for tensor copies for now; investigate
        # the perf with/without it.
        with torch.profiler.record_function("FullyShardedDataParallel._to_kwargs"):
            args_tuple, kwargs_tuple = _to_kwargs(
                args, kwargs, state.compute_device, False
            )
        args = args_tuple[0] if args_tuple else ()
        kwargs = kwargs_tuple[0] if kwargs_tuple else {}

        return _root_cast_forward_input(state, module, args, kwargs)