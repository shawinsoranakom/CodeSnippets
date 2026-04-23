def _find_nd_overlapping_shards(
    shards: list[ShardMetadata], sharded_dims: list[int]
) -> tuple[int, int] | None:
    """Find overlapping shards using sweep-line algorithm."""
    if len(shards) <= 1:
        return None

    dims = len(sharded_dims)
    if dims == 0:
        return None

    sweep_dim_idx = 0
    if dims > 1:
        max_size = 0
        for i, dim in enumerate(sharded_dims):
            dim_size = shards[0].shard_offsets[dim] + shards[0].shard_sizes[dim]
            if dim_size > max_size:
                max_size = dim_size
                sweep_dim_idx = i
    sweep_dim = sharded_dims[sweep_dim_idx]

    sorted_indices = sorted(
        range(len(shards)),
        key=lambda idx: (
            shards[idx].shard_offsets[sweep_dim],
            *(shards[idx].shard_offsets[d] for d in sharded_dims if d != sweep_dim),
        ),
    )
    active: list[tuple[int, int]] = []

    for idx in sorted_indices:
        current = shards[idx]
        start = current.shard_offsets[sweep_dim]
        end = start + current.shard_sizes[sweep_dim]

        cutoff = bisect_right(active, (start, sys.maxsize))
        if cutoff:
            del active[:cutoff]

        for _, other_idx in active:
            other = shards[other_idx]

            if _check_shard_metadata_pair_overlap(current, other):
                return (other_idx, idx)
        insort(active, (end, idx))
    return None