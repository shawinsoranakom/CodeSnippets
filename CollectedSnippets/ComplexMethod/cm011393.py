def redistribute_cost(
    current_spec: "dtensor_spec.DTensorSpec",
    target_spec: "dtensor_spec.DTensorSpec",
) -> float:
    """
    This function returns the cost of redistribute from current to target DTensorSpec.

    NOTE:
    1. Only consider communication cost here, since computation costs for redistribute
       are quite trivial (i.e. we only need to narrow or simple division)
    2. Only consider redistribute cost on same mesh, cross mesh communication cost is
       not quite needed for operator strategy estimation/selection.
    """
    if current_spec.mesh != target_spec.mesh:
        # make infinite cost if meshes are not same
        # TODO: see if we want to support this once there's cross mesh communication
        return float("inf")
    if current_spec.is_replicated():
        # short-cut: comm cost is 0 if current spec is already full replication
        return 0.0

    # TODO(zpcore): test placements with _StridedShard if we replace shard_order
    # with _StridedShard.
    if (
        current_spec.placements == target_spec.placements
        and current_spec.shard_order == target_spec.shard_order
    ):
        return 0.0

    # For sub-meshes, ranks not participating in the mesh should not compute
    # redistribution costs. Return 0 since they won't actually participate.
    if not current_spec.mesh._is_current_rank_part_of_mesh():
        return 0.0

    mesh_topo = MeshTopoInfo.build_from_mesh(current_spec.mesh)
    cost = 0.0
    comm_bytes_gb = (
        spec_to_bytes(current_spec) / current_spec.num_shards / 1024 / 1024 / 1024
    )
    # Transformation that considered for redistribute cost:
    # 1. allgather 2. alltoall
    # 3. allreduce 4. reduce_scatter
    from torch.distributed._functional_collectives import _are_we_tracing
    from torch.distributed.tensor._redistribute import (
        _gen_transform_infos,
        _gen_transform_infos_non_cached,
    )

    # TODO(zpcore): Support _StridedShard redistribution. Remove the temporary
    # fix, which is to prevent StridedShard erroring out.
    if current_spec.shard_order is None or target_spec.shard_order is None:
        return float("inf")

    # No redistribution needed when placements are already identical.
    # This also prevents potential failures in _gen_transform_infos for certain configurations
    # (e.g., sub-meshes) where finding a transform path between identical states may error out.
    # TODO(zpcore): test placements with _StridedShard if we replace shard_order
    # with _StridedShard.
    if (
        current_spec.placements == target_spec.placements
        and current_spec.shard_order == target_spec.shard_order
    ):
        return cost

    if _are_we_tracing():
        transform_infos = _gen_transform_infos_non_cached(current_spec, target_spec)
    else:
        transform_infos = _gen_transform_infos(current_spec, target_spec)
    for transform_info in transform_infos:
        if current_spec.tensor_meta is None:
            raise AssertionError("spec should have tensor meta defined!")
        current = transform_info.src_dst_placements[0]
        target = transform_info.src_dst_placements[1]
        mesh_dim = transform_info.mesh_dim
        step_cost, comm_bytes_gb = _compute_placement_transition_cost(
            current, target, mesh_topo, mesh_dim, comm_bytes_gb
        )
        if step_cost == float("inf"):
            return float("inf")
        cost += step_cost

    return cost