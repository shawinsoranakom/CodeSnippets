def _init_param_group(
    state: "FSDPState",
    params: list[nn.Parameter],
    modules: tuple[nn.Module, ...],
    mesh_info: DataParallelMeshInfo,
    post_forward_mesh_info: FSDPMeshInfo | None,
    device: torch.device,
    shard_placement_fn: "Callable[[nn.Parameter], ShardPlacementFnResult] | None",
    mp_policy: "MixedPrecisionPolicy",
    offload_policy: "OffloadPolicy",
    reshard_after_forward: bool | int = True,
) -> None:
    """
    Initialize FSDP param groups for the given state.

    Params are grouped by their process group (derived from ``mesh_info`` via
    ``shard_placement_fn``). Each group becomes a separate ``FSDPParamGroup``.
    When ``shard_placement_fn`` is ``None`` or returns the same mesh for all
    params, this creates a single group.
    """
    # Import here to avoid circular imports
    from ._fsdp_common import FSDPMeshInfo, resolve_shard_placement
    from ._fsdp_param_group import FSDPParamGroup

    if not params:
        return

    if shard_placement_fn is None:
        # No shard_placement_fn means all params use the same mesh_info,
        # so no grouping is needed. This also handles DDPMeshInfo from
        # replicate_with_fsdp, which doesn't have shard_process_group.
        state._fsdp_param_groups.append(
            FSDPParamGroup(
                params,
                modules,
                mesh_info,
                post_forward_mesh_info,
                device,
                shard_placement_fn,
                mp_policy,
                offload_policy,
            )
        )
        return

    # Group params by their process group to support per-param mesh,
    # e.g., expert params using ep_mesh vs regular params using dp_mesh.
    # For HSDP, also key by replicate_process_group to avoid grouping
    # FSDPMeshInfo params with HSDPMeshInfo params that share the same
    # shard_process_group but require different gradient reduction behavior.
    if not isinstance(mesh_info, FSDPMeshInfo):
        raise ValueError(
            "Per-param mesh via shard_placement_fn is not supported with "
            f"{type(mesh_info).__name__}; it requires FSDPMeshInfo (or subclass)"
        )
    pg_to_group: dict[
        tuple[dist.ProcessGroup, dist.ProcessGroup | None],
        tuple[FSDPMeshInfo, list[nn.Parameter]],
    ] = {}
    for param in params:
        param_mesh_info = resolve_shard_placement(
            shard_placement_fn(param),
            mesh_info,
        ).mesh_info
        shard_pg = param_mesh_info.shard_process_group
        replicate_pg: dist.ProcessGroup | None = None
        if isinstance(param_mesh_info, HSDPMeshInfo):
            replicate_pg = param_mesh_info.replicate_process_group
        key = (shard_pg, replicate_pg)
        if key not in pg_to_group:
            pg_to_group[key] = (param_mesh_info, [param])
        else:
            existing_mesh_info = pg_to_group[key][0]
            if existing_mesh_info is not param_mesh_info:
                raise ValueError(
                    f"Params sharing the same process group must use the same "
                    f"FSDPMeshInfo object, but got different objects: "
                    f"{existing_mesh_info} vs {param_mesh_info}"
                )
            pg_to_group[key][1].append(param)

    # Create a FSDPParamGroup per process group
    for group_mesh_info, group_params in pg_to_group.values():
        if group_mesh_info is not mesh_info:
            group_post_forward = _get_post_forward_mesh_info(
                reshard_after_forward, group_mesh_info
            )
        else:
            group_post_forward = post_forward_mesh_info
        state._fsdp_param_groups.append(
            FSDPParamGroup(
                group_params,
                modules,
                group_mesh_info,
                group_post_forward,
                device,
                shard_placement_fn,
                mp_policy,
                offload_policy,
            )
        )