def one_step_redistribute_cost(
    current_spec: "dtensor_spec.DTensorSpec",
    target_spec: "dtensor_spec.DTensorSpec",
) -> float:
    """
    Calculate the cost of a single redistribution step between two DTensorSpecs.

    This function computes the communication cost for a one-step redistribution
    where the current and target specs differ by exactly one placement on one
    mesh dimension.

    Args:
        current_spec: The current DTensorSpec.
        target_spec: The target DTensorSpec.

    Returns:
        The communication cost for this step (float("inf") if invalid).
    """
    if current_spec.mesh != target_spec.mesh:
        return float("inf")

    if current_spec.placements == target_spec.placements:
        return 0.0

    # Find the mesh dimension that differs
    mesh_dim = -1
    current_placement = None
    target_placement = None
    for i, (cur, tgt) in enumerate(
        zip(current_spec.placements, target_spec.placements)
    ):
        if cur != tgt:
            if mesh_dim != -1:
                # More than one dimension differs - not a single step
                raise ValueError(
                    "one_step_redistribute_cost expects specs that differ by exactly one placement"
                )
            mesh_dim = i
            current_placement = cur
            target_placement = tgt

    if mesh_dim == -1:
        return 0.0

    if current_placement is None or target_placement is None:
        raise AssertionError

    mesh_topo = MeshTopoInfo.build_from_mesh(current_spec.mesh)
    comm_bytes_gb = (
        spec_to_bytes(current_spec) / current_spec.num_shards / 1024 / 1024 / 1024
    )

    cost, _ = _compute_placement_transition_cost(
        current_placement, target_placement, mesh_topo, mesh_dim, comm_bytes_gb
    )
    return cost