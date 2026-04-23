def _update_shard_order_and_placements(
    transform_info: _TransformInfo,
    current_placements: list[Placement],
    shard_order_dict: dict[int, list[int]],
) -> None:
    """
    Update current_placements and shard_order_dict in-place to reflect the
    effect of a single transform step.
    """
    src_placement, dst_placement = transform_info.src_dst_placements

    if isinstance(transform_info, _FlattenedTransformInfo):
        mesh_dims = transform_info.original_mesh_dims
    else:
        mesh_dims = (transform_info.mesh_dim,)

    if isinstance(src_placement, Shard | _StridedShard):
        src_dim = src_placement.dim  # type: ignore[attr-defined]
        removed_dim = set()
        for _ in mesh_dims:
            if len(shard_order_dict[src_dim]) == 0:
                raise ValueError(
                    "Invalid shard_order update. No entries left to pop for src_dim "
                    f"{src_dim}. transform_info={transform_info}, "
                    f"current_placements={current_placements}, "
                    f"shard_order={shard_order_dict}"
                )
            removed_dim.add(shard_order_dict[src_dim].pop())

        if not set(mesh_dims) == removed_dim:
            raise ValueError(
                "Mismatch between expected and removed mesh dims during shard_order "
                "update. Expected to remove "
                f"{set(mesh_dims)}, but removed {removed_dim}. "
                f"transform_info={transform_info}, "
                f"current_placements={current_placements}, "
                f"shard_order={shard_order_dict}"
            )
    if isinstance(dst_placement, Shard | _StridedShard):
        dst_dim = dst_placement.dim  # type: ignore[attr-defined]
        if dst_dim not in shard_order_dict:
            shard_order_dict[dst_dim] = []
        for mesh_dim in mesh_dims:
            shard_order_dict[dst_dim].append(mesh_dim)

    for mesh_dim in mesh_dims:
        current_placements[mesh_dim] = dst_placement