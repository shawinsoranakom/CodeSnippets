def _compute_placement_transition_cost(
    current_placement: "dtensor_spec.Placement",
    target_placement: "dtensor_spec.Placement",
    mesh_topo: MeshTopoInfo,
    mesh_dim: int,
    comm_bytes_gb: float,
) -> tuple[float, float]:
    """
    Compute the cost of transitioning from one placement to another on a single mesh dimension.

    Args:
        current_placement: The current placement on the mesh dimension.
        target_placement: The target placement on the mesh dimension.
        mesh_topo: Mesh topology information for cost estimation.
        mesh_dim: The mesh dimension where the transition happens.
        comm_bytes_gb: The communication bytes in GB for this step.

    Returns:
        A tuple of (cost, updated_comm_bytes_gb):
            - cost: The communication cost for this transition (float("inf") if invalid).
            - updated_comm_bytes_gb: The updated communication bytes after this step.
    """
    if current_placement == target_placement:
        return 0.0, comm_bytes_gb

    num_devices_on_mesh_dim = mesh_topo.mesh_dim_devices[mesh_dim]

    # NOTE: is_shard() does not match _StridedShard; see _is_shard_like().
    # Safe today: redistribute_cost bails with inf when shard_order is None.
    if current_placement.is_shard() and target_placement.is_replicate():
        # allgather gives larger comm bytes
        comm_bytes_gb *= num_devices_on_mesh_dim
        return allgather_cost(comm_bytes_gb, mesh_topo, mesh_dim), comm_bytes_gb
    elif current_placement.is_shard() and target_placement.is_shard():
        # should be alltoall comm, since we haven't implement it yet, add 1.0 as penalty
        # to favor allgather instead
        # TODO: add alltoall_cost
        return allgather_cost(comm_bytes_gb, mesh_topo, mesh_dim) + 1.0, comm_bytes_gb
    elif current_placement.is_partial() and target_placement.is_replicate():
        return allreduce_cost(comm_bytes_gb, mesh_topo, mesh_dim), comm_bytes_gb
    elif current_placement.is_partial() and target_placement.is_shard():
        cost = reduce_scatter_cost(comm_bytes_gb, mesh_topo, mesh_dim)
        # after reduce_scatter the comm bytes for further collectives halved.
        comm_bytes_gb /= num_devices_on_mesh_dim
        return cost, comm_bytes_gb
    elif current_placement.is_shard() and target_placement.is_partial():
        # ban shard -> partial as it does not make sense to perform
        # this redistribute
        return float("inf"), comm_bytes_gb
    elif current_placement.is_partial() and target_placement.is_partial():
        # we already handled the == case at the top, and we ban converting between partial types.
        return float("inf"), comm_bytes_gb
    elif current_placement.is_replicate() and target_placement.is_shard():
        comm_bytes_gb /= num_devices_on_mesh_dim
        return 0.0, comm_bytes_gb

    return 0.0, comm_bytes_gb