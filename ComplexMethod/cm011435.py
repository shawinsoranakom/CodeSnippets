def _warn_flatten_optimization_not_possible(
    device_mesh: DeviceMesh,
    mesh_dims: tuple[int, ...],
    src_placements: tuple[Placement, ...],
    dst_placements: tuple[Placement, ...],
    num_ops: int,
    comm_type: str,
    reason: str,
) -> None:
    """
    Warn once per (mesh, dims, reason) about inability to flatten operations.

    Args:
        device_mesh: The device mesh being used
        mesh_dims: Tuple of mesh dimensions that could not be flattened
        src_placements: Source placements for the redistribution
        dst_placements: Target placements for the redistribution
        num_ops: Number of sequential operations that will be performed
        comm_type: Type of collective operation (e.g., "reduce_scatter")
        reason: Either "no_flattened_mesh" or "uneven_tensor_shape"
    """
    cache_key = (hash(device_mesh), mesh_dims, reason)
    if cache_key in _warned_flatten_issues:
        return
    _warned_flatten_issues.add(cache_key)

    mesh_dim_names = device_mesh.mesh_dim_names
    if mesh_dim_names is not None:
        dim_names = [mesh_dim_names[d] for d in mesh_dims]
        dims_str = ", ".join(f'"{name}"' for name in dim_names)
    else:
        dims_str = f"dims {', '.join(str(d) for d in mesh_dims)} of {device_mesh}"

    common_warning = (
        "While redistributing from %s to %s, %d sequential %s "
        "operations will be performed. This is suboptimal: "
        "multiple collective operations have higher latency "
        "(separate kernel launches and synchronization points) "
        "and may give inconsistent results between ranks due to different reduction orders. %s"
    )

    if reason == "no_flattened_mesh":
        reason_msg = f"To optimize, flatten mesh dimensions [{dims_str}] so DTensor can use a single operation instead."
    elif reason == "uneven_tensor_shape":
        reason_msg = (
            " Unfortunately, because the tensor dimension is not evenly divisible by the product of "
            "the mesh dim sizes that would need to be flattened for the optimization to work, it can not be optimized.",
        )
    elif reason == "non_ascending_mesh_dims":
        reason_msg = (
            f"it is not possible to merge non-ascending order {comm_type} operations."
        )
    else:
        raise AssertionError(f"Unexpected reason: {reason}")

    logger.warning(
        common_warning, src_placements, dst_placements, num_ops, comm_type, reason_msg
    )