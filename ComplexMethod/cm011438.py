def redistribute_local_tensor(
    local_tensor: torch.Tensor,
    current_spec: DTensorSpec,
    target_spec: DTensorSpec,
    *,
    async_op: bool = False,
    use_graph_based_transform: bool | None = None,
    # True if user explicitly called DTensor.redistribute()
    is_explicit: bool = False,
) -> torch.Tensor:
    """
    This redistribute the local tensor (torch.Tensor) from the current DTensorSpec to
    the target DTensorSpec, which involves the necessary collective calls to transform
    the local shard of the DTensor from its current spec to the target spec.
    """

    if current_spec.mesh != target_spec.mesh:
        # TODO: alltoall/permute reshuffling to change device_mesh if they are not the same
        raise NotImplementedError("Cross device mesh comm not supported yet!")

    if current_spec.use_strided_shard_as_shard_order is None:
        raise ValueError(
            "use_strided_shard_as_shard_order should be initialized in DTensorSpec.__post_init__()"
        )

    # We do not see a valid use case for mixing different partial types in the same DTensor.
    # in principle it could be supported, but since nonlinear reductions (e.g. max) exist, relative ordering
    # of different partials would become semantically critical.  Without a motivating use case, we prohibit this.
    assert_no_mixed_partial_types(current_spec.placements)
    assert_no_mixed_partial_types(target_spec.placements)

    new_local_tensor = local_tensor
    device_mesh = current_spec.mesh

    if not device_mesh._is_current_rank_part_of_mesh():
        # if rank is not part of mesh, we skip redistribute and simply return local_tensor,
        # which should be an empty tensor
        return local_tensor

    if _are_we_tracing():
        transform_infos = _gen_transform_infos_non_cached(
            current_spec, target_spec, use_graph_based_transform
        )
    else:
        transform_infos = _gen_transform_infos(
            current_spec, target_spec, use_graph_based_transform
        )

    # Optimize by grouping same-type collectives into flattened operations
    optimized_transform_infos = _optimize_transform_infos(
        transform_infos,
        device_mesh,
        current_spec.placements,
        target_spec.placements,
    )

    debug_mode = get_active_debug_mode()

    redistribute_context = (
        debug_mode.record_redistribute_calls(  # type: ignore[union-attr]
            local_tensor,
            current_spec.placements,
            target_spec.placements,
            DTensorRedistributePlanner.stringify_transform_infos(
                device_mesh,
                optimized_transform_infos,
                current_spec.placements,
                current_spec.shard_order,
                current_spec.use_strided_shard_as_shard_order,
            ),
            is_explicit=is_explicit,
        )
        if debug_mode is not None
        else contextlib.nullcontext()
    )

    with redistribute_context:
        for transform_info in optimized_transform_infos:
            # Determine which mesh to use: flattened transforms have their own mesh
            if isinstance(transform_info, _FlattenedTransformInfo):
                mesh_to_use = transform_info.mesh
            else:
                mesh_to_use = device_mesh
            i = transform_info.mesh_dim
            current, target = transform_info.src_dst_placements

            # _StridedShard methods use device_mesh directly, not mesh_to_use.
            # This is safe because _StridedShard.is_shard() returns False, so
            # _comm_type_key() returns None and flattening is never attempted.
            if isinstance(current, _StridedShard) or isinstance(target, _StridedShard):
                assert mesh_to_use is device_mesh, (  # noqa: S101
                    "_StridedShard redistribute assumes no flattened transforms"
                )

            num_chunks = mesh_to_use.size(mesh_dim=i)

            if current == target:
                # short cut, just use the original local tensor
                new_local_tensor = local_tensor
                continue

            if num_chunks == 1:
                # short cut, if there's only one shard, we don't need to do any collective
                # comm, just use the original local tensor
                new_local_tensor = local_tensor
                continue

            if target.is_replicate():
                # Case 1: target is Replicate
                if current.is_partial():
                    partial_spec = cast(Partial, current)
                    new_local_tensor = partial_spec._reduce_value(
                        local_tensor, mesh_to_use, i
                    )
                    # For merged sum/avg partials, apply avg scaling
                    if (
                        isinstance(transform_info, _FlattenedTransformInfo)
                        and transform_info.avg_scale is not None
                    ):
                        new_local_tensor = new_local_tensor / transform_info.avg_scale
                elif current.is_shard():
                    current_placement = cast(Shard, current)
                    new_local_tensor = current_placement._to_replicate_tensor(
                        local_tensor, mesh_to_use, i, transform_info.logical_shape
                    )
                elif isinstance(current, _StridedShard):
                    new_local_tensor = current._to_replicate_tensor(
                        local_tensor, device_mesh, i, transform_info.logical_shape
                    )
                else:
                    raise RuntimeError(
                        f"redistribute from {current} to {target} not supported yet"
                    )

            elif target.is_shard():
                # Case 2: target is Shard
                target_placement = cast(Shard, target)
                if current.is_partial():
                    partial_spec = cast(Partial, current)
                    new_local_tensor = partial_spec._reduce_shard_value(
                        local_tensor, mesh_to_use, i, target_placement
                    )
                    # For merged sum/avg partials, apply avg scaling
                    if (
                        isinstance(transform_info, _FlattenedTransformInfo)
                        and transform_info.avg_scale is not None
                    ):
                        new_local_tensor = new_local_tensor / transform_info.avg_scale
                elif current.is_replicate():
                    # split the tensor and return the corresponding cloned local shard
                    new_local_tensor = target_placement._replicate_to_shard(
                        local_tensor, mesh_to_use, i, mesh_to_use._sym_get_coordinate(i)
                    )
                elif current.is_shard():
                    shard_spec = cast(Shard, current)
                    if shard_spec.dim != target_placement.dim:
                        new_local_tensor = shard_spec._to_new_shard_dim(
                            local_tensor,
                            mesh_to_use,
                            i,
                            transform_info.logical_shape,
                            target_placement.dim,
                        )
                elif isinstance(current, _StridedShard):
                    # _StridedShard -> Shard: go via Replicate as intermediate
                    replicated = current._to_replicate_tensor(
                        local_tensor, device_mesh, i, transform_info.logical_shape
                    )
                    new_local_tensor = target_placement._replicate_to_shard(
                        replicated,
                        mesh_to_use,
                        i,
                        mesh_to_use._sym_get_coordinate(i),
                    )
                else:
                    raise ValueError(
                        f"Unexpected placement {current} for redistribute to target placement {target}"
                    )
            elif target.is_partial():
                if current.is_replicate():
                    partial_spec = cast(Partial, target)
                    new_local_tensor = partial_spec._partition_value(
                        local_tensor, mesh_to_use, i
                    )
                elif _is_shard_like(current):
                    raise RuntimeError(
                        f"redistribute from {current} to {target} not supported yet"
                    )
                else:
                    if current != target:
                        raise AssertionError(
                            f"Redistribution from one partial type ({current}) to another ({target}) is unsupported."
                        )
                    # partial -> partial no op, should never hit
                    new_local_tensor = local_tensor
            elif isinstance(target, _StridedShard):
                # Case 4: target is _StridedShard
                if current.is_partial():
                    # Partial -> _StridedShard: reduce to Replicate, then strided shard
                    partial_spec = cast(Partial, current)
                    replicated = partial_spec._reduce_value(
                        local_tensor, mesh_to_use, i
                    )
                    new_local_tensor = target._replicate_to_strided_shard(
                        replicated, device_mesh, i, device_mesh._sym_get_coordinate(i)
                    )
                elif current.is_replicate():
                    # split the tensor and return the corresponding local strided shard
                    new_local_tensor = target._replicate_to_strided_shard(
                        local_tensor, device_mesh, i, device_mesh._sym_get_coordinate(i)
                    )
                elif current.is_shard():
                    # Shard -> _StridedShard: all-gather to Replicate, then strided shard
                    current_placement = cast(Shard, current)
                    replicated = current_placement._to_replicate_tensor(
                        local_tensor, mesh_to_use, i, transform_info.logical_shape
                    )
                    new_local_tensor = target._replicate_to_strided_shard(
                        replicated, device_mesh, i, device_mesh._sym_get_coordinate(i)
                    )
                elif isinstance(current, _StridedShard):
                    # _StridedShard -> _StridedShard: go through Replicate
                    # First convert to Replicate, then to _StridedShard
                    replicated = current._to_replicate_tensor(
                        local_tensor, device_mesh, i, transform_info.logical_shape
                    )
                    new_local_tensor = target._replicate_to_strided_shard(
                        replicated, device_mesh, i, device_mesh._sym_get_coordinate(i)
                    )
                else:
                    raise ValueError(
                        f"Unexpected placement {current} for redistribute to target placement {target}"
                    )

            if not async_op and isinstance(
                new_local_tensor, funcol.AsyncCollectiveTensor
            ):
                new_local_tensor = new_local_tensor.wait()
            local_tensor = new_local_tensor
    return new_local_tensor