def _init_process_group_state(
    state: _FSDPState,
    process_group: ProcessGroupType,
    sharding_strategy: ShardingStrategy,
    policy: _Policy | None,
    device_mesh: DeviceMesh | None = None,
) -> _FSDPState:
    if process_group is not None and device_mesh is not None:
        raise ValueError(
            "Cannot pass both process_group and device_mesh at the "
            "same time. Please just pass only one of them."
        )
    is_hybrid_strategy = sharding_strategy in HYBRID_SHARDING_STRATEGIES
    if is_hybrid_strategy:
        if process_group is None and policy is None and device_mesh is None:
            # Raise an error here, since this is manual wrapping with no process group
            # passed in, there is no way to ensure all wrapped FSDP instances use the same
            # process groups.
            raise ValueError(
                f"Manual wrapping with {sharding_strategy} "
                "requires explicit specification of process group or device_mesh."
            )
        else:
            state = _init_process_group_state_for_hybrid_shard(
                state, process_group, device_mesh
            )
    else:
        if device_mesh:
            state._device_mesh = device_mesh
            state.process_group = device_mesh.get_group(mesh_dim=0)
        else:
            state.process_group = (
                process_group if process_group is not None else _get_default_group()
            )

    state.rank = state.process_group.rank()
    state.world_size = state.process_group.size()
    data_parallel_world_size = state.world_size
    if is_hybrid_strategy:
        data_parallel_world_size *= state._inter_node_pg.size()
    state._gradient_predivide_factor = (
        default_hooks.DefaultState._get_gradient_predivide_factor(
            data_parallel_world_size
        )
    )
    state._gradient_postdivide_factor = (
        data_parallel_world_size / state._gradient_predivide_factor
    )
    return state