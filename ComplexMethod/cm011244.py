def _infer_sharding_spec_from_shards_metadata(shards_metadata):
    """
    Infer the sharding spec from the metadata of each shard of a ShardedTensor.
    If the tensor is sharded only on one dimension, we can then verify whether it's
    a ChunkShardingSpec or not. The way to verify it is to first get the total length
    and perform a chunk sharding with the given placements to see if we can have the
    same chunk size as the given shards_metadata. If not, we assume it's enum sharded.

    Args:
        shards_metadata (List[ShardMetadata]): List of Metadata of local shards.

    Returns:
        A :class:`torch.distributed._shard.sharding_spec.ShardingSpec` object of sharding
            spec for one sharded tensor.
    """
    placements = []
    chunk_sharding_dim = None
    chunk_offset_list = []
    shard_size_list = []
    shard_offset_list = []
    # collect local shard metadatas from the global sharded_tensor_metadata
    for shard_metadata in shards_metadata:  # type: ignore[attr-defined]
        placements.append(shard_metadata.placement)
        local_offsets = shard_metadata.shard_offsets
        chunk_offset_list.append(sum(local_offsets))
        shard_size_list.append(shard_metadata.shard_sizes)
        shard_offset_list.append(shard_metadata.shard_offsets)
        shard_dims = [idx for idx, e in enumerate(local_offsets) if e != 0]
        # If the offset is [0, 0, ..., 0] (all zeros),
        # we cannot decide whether how the tensor is sharded.
        if len(shard_dims) == 0:
            continue
        # If the offset is [0, N, .,0, M, 0, .., 0],
        # we are sure it's sharded by more than one dimension.
        if len(shard_dims) != 1:
            chunk_sharding_dim = None
            break
        # If the offset is [0, 0, .,0, M, 0, .., 0], aka, it's sharded by just
        # one dimension, we need to make sure all ranks share the same dimension.
        if not chunk_sharding_dim:
            chunk_sharding_dim = shard_dims[0]
        elif chunk_sharding_dim != shard_dims[0]:
            chunk_sharding_dim = None
            break

    if chunk_sharding_dim is not None:
        # Ensure we infer the correct placement order from offsets
        placements = [
            x
            for _, x in sorted(
                zip(chunk_offset_list, placements), key=operator.itemgetter(0)
            )
        ]

        from .chunk_sharding_spec import ChunkShardingSpec

        chunk_spec = ChunkShardingSpec(
            dim=chunk_sharding_dim,
            placements=placements,
        )

        shard_sizes = sorted([x[chunk_sharding_dim] for x in shard_size_list])
        shard_total_length = sum(shard_sizes)
        shard_offsets = sorted([x[chunk_sharding_dim] for x in shard_offset_list])

        chunks = len(placements)
        split_size = get_split_size(shard_total_length, chunks)
        chunk_shard_sizes = sorted(
            [
                get_chunked_dim_size(shard_total_length, split_size, idx)
                for idx in range(chunks)
            ]
        )
        # Should match ChunkShardingSpec offsets calculation
        chunk_shard_offsets = [split_size * idx for idx in range(chunks)]
        if shard_sizes == chunk_shard_sizes and shard_offsets == chunk_shard_offsets:
            return chunk_spec
    return EnumerableShardingSpec(shards_metadata)