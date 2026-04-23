def map_placements_after_reduction(
    placements: tuple[Placement, ...],
    reduction_dims: list[int],
    reduction_dims_map: list[int],
    reduction_op: ReductionOpType,
) -> tuple[Placement, ...]:
    """
    Map each placement based on the output shape after reduction.
    """
    new_placements: list[Placement] = []
    for placement in placements:
        if isinstance(placement, (Replicate, Partial)):
            new_placements.append(placement)
        else:
            if not _is_shard_like(placement):
                raise AssertionError(
                    f"Expected Shard/_StridedShard, got {type(placement)}"
                )
            shard_dim = placement.dim
            new_shard_dim = reduction_dims_map[shard_dim]
            if new_shard_dim == -1 or shard_dim in reduction_dims:
                # if new_shard_dim collapsed or its in the reduction dims
                # (i.e. for the case where keepdims=True), we generate partial
                new_placements.append(get_placement_from_reduction_op(reduction_op))
            else:
                if isinstance(placement, _StridedShard):
                    new_placements.append(
                        _StridedShard(
                            new_shard_dim, split_factor=placement.split_factor
                        )
                    )
                elif isinstance(placement, Shard):
                    new_placements.append(Shard(new_shard_dim))
    return tuple(new_placements)