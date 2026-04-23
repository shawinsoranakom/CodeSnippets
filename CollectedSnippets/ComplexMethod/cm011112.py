def _init_param_handle_from_module(
    state: _FSDPState,
    fully_sharded_module: nn.Module,
    device_id: int | torch.device | None,
    param_init_fn: Callable[[nn.Module], None] | None,
    sync_module_states: bool,
) -> _FSDPState:
    """Initialize a ``FlatParamHandle`` from a module ``fully_sharded_module``."""
    _check_single_device_module(fully_sharded_module, state._ignored_params, device_id)
    device_from_device_id = _get_device_from_device_id(
        device_id, state.rank, state._device_handle
    )
    is_meta_module, is_torchdistX_deferred_init = _need_to_materialize_module(
        fully_sharded_module, state._ignored_params, state._ignored_modules
    )
    # Materialize the module if needed
    if (is_meta_module or is_torchdistX_deferred_init) and param_init_fn is not None:
        _materialize_with_param_init_fn(
            fully_sharded_module, param_init_fn, state._ignored_modules
        )
    elif is_meta_module:
        _materialize_meta_module(
            fully_sharded_module,
            device_id,
            state._ignored_modules,
            state._device_handle,
        )
    elif is_torchdistX_deferred_init:
        deferred_init.materialize_module(
            fully_sharded_module,
            check_fn=lambda submodule: _get_module_fsdp_state(submodule) is None
            and submodule not in state._ignored_modules,
        )

    ignored_buffers = {
        buffer
        for ignored_module in state._ignored_modules
        for buffer in ignored_module.buffers()
    }

    _move_module_to_device(
        fully_sharded_module,
        state._ignored_params,
        ignored_buffers,
        device_from_device_id,
    )
    state.compute_device = _get_compute_device(
        fully_sharded_module,
        state._ignored_params,
        device_from_device_id,
        state.rank,
        state._device_handle,
    )

    managed_params = list(_get_orig_params(fully_sharded_module, state._ignored_params))
    _verify_managed_params(fully_sharded_module, managed_params)
    if sync_module_states:
        if state.sharding_strategy in HYBRID_SHARDING_STRATEGIES:
            # Broadcast inter-node first, then intra-node. The inter-node
            # broadcast propagates rank 0's states to each node's local
            # rank 0, so the subsequent intra-node broadcast has the
            # correct source values on every node. Reversing this order
            # causes local rank 0 on non-source nodes to broadcast
            # uninitialized states (e.g. from meta-device materialization).
            _sync_module_params_and_buffers(
                fully_sharded_module, managed_params, state._inter_node_pg
            )
            # _sync_module_params_and_buffers marks each buffer with
            # FSDP_SYNCED=True to avoid redundant syncs in nested
            # wrapping. Reset the flag here so the intra-node broadcast
            # below also includes buffers.
            for buffer in fully_sharded_module.buffers():
                if hasattr(buffer, FSDP_SYNCED):
                    setattr(buffer, FSDP_SYNCED, False)
        _sync_module_params_and_buffers(
            fully_sharded_module, managed_params, state.process_group
        )
    _init_param_handle_from_params(state, managed_params, fully_sharded_module)
    return state