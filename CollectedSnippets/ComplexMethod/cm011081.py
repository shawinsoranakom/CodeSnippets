def _init_streams(
    state: _FSDPState,
) -> None:
    """
    Initializes CUDA streams for overlapping communication, computation, and
    data transfers. The streams should be shared across FSDP instances.
    """
    if not state._is_root:
        raise AssertionError("Expected state to be root")
    if not state._device_handle.is_available():
        raise AssertionError("Expected device handle to be available")
    uses_hybrid_sharding = any(
        fsdp_state.sharding_strategy in HYBRID_SHARDING_STRATEGIES
        for fsdp_state in state._all_fsdp_states
    )
    # Prioritize all-gathers/reduce-scatters over async all-reduce for HSDP and
    # preserve the default priority of 0 otherwise
    high_priority = -1 if state.limit_all_gathers and uses_hybrid_sharding else 0
    # Default stream for computation
    state._default_stream = state._device_handle.current_stream()
    if state._fsdp_extension is not None:
        # set the compute stream to the FSDP extension
        state._fsdp_extension.compute_stream = state._default_stream

    # Stream for unshard logic, including allocating the all-gather destination
    # tensors and the all-gathers themselves
    state._unshard_stream = state._device_handle.Stream(priority=high_priority)
    # Stream for overlapping gradient reduction with the backward pass gradient
    # computation
    state._post_backward_stream = state._device_handle.Stream(priority=high_priority)
    # Stream for pre-unshard logic, namely allocations and writes for CPU
    # offloading (H2D copy) and mixed precision (low precision cast)
    state._pre_unshard_stream = state._device_handle.Stream(priority=high_priority)
    # Stream to run HSDP's all-reduce as async (if using HSDP)
    state._all_reduce_stream = (
        state._device_handle.Stream() if uses_hybrid_sharding else state._default_stream
    )