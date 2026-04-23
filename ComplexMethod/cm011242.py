def validate_non_overlapping_shards_metadata(shards: list[ShardMetadata]):
    """
    Ensures none of the shards overlap with each other.

    Args:
        shards(List[ShardMetadata]): List of :class:`ShardMetadata` objects representing
            each shard.
    Raises:
        ``ValueError`` if there's overlap in any two shards.
    """
    if not shards or len(shards) == 1:
        return

    sharded_dims: list[int] = []
    for dim in range(len(shards[0].shard_offsets)):
        for i in range(1, len(shards)):
            if (
                shards[i].shard_offsets[dim] != shards[0].shard_offsets[dim]
                or shards[i].shard_sizes[dim] != shards[0].shard_sizes[dim]
            ):
                sharded_dims.append(dim)
                break

    pair: tuple[int, int] | None = None
    if len(sharded_dims) == 0:
        # if shard is all zeros, we should consider as pass
        all_zeros: bool = all(
            # strictly limited all offsets to be 0 to pass
            # could loose it later on
            shard.shard_offsets == [0] * len(shards[0].shard_offsets)
            and math.prod(shard.shard_sizes) == 0  # one dimension is 0
            for shard in shards
        )
        if all_zeros:
            return
        # All shards are the same, all dims are not partitioned. Choose any 2.
        pair = (0, 1)
    elif len(sharded_dims) == 1:
        # Shards are partitioned over only one dimension. Overlap can be found
        # using a O(nlogn) overlapping interval algorithm.
        pair = _find_1d_overlapping_shards(shards, sharded_dims[0])
    else:
        # Shards are partitioned over more than one dimension.
        # Use sweep-line algorithm for O(n log n) complexity.
        pair = _find_nd_overlapping_shards(shards, sharded_dims)

    if pair:
        raise ValueError(f"Shards {shards[pair[0]]} and {shards[pair[1]]} overlap")