def recalc_global_sharded_tensor_metadata(
    global_sharded_tensor_metadata: ShardedTensorMetadata, sharded_dim: int
) -> None:
    # recalculate global ShardedTensorMetadata

    # reorder here in case shard metadata is not sorted on sharded_dim
    placement_idx_pairs = []
    for i, shard_metadata in enumerate(global_sharded_tensor_metadata.shards_metadata):
        if shard_metadata.placement:
            placement_idx_pairs.append((shard_metadata.placement.rank(), i))
        else:
            raise AssertionError(
                "currently only support rw, it should always have valid rank info"
            )
    sorted_idx = sorted(placement_idx_pairs)
    shard_sizes = [
        global_sharded_tensor_metadata.shards_metadata[idx].shard_sizes[sharded_dim]
        for _, idx in sorted_idx
    ]
    cum_sum = [0] + list(itertools.accumulate(shard_sizes))

    for shard_id, shard_metadata in enumerate(
        global_sharded_tensor_metadata.shards_metadata
    ):
        # update shard offset for each shard on the sharded dimension
        shard_metadata.shard_offsets[sharded_dim] = cum_sum[shard_id]
        for other_dim in range(
            len(global_sharded_tensor_metadata.shards_metadata[0].shard_sizes)
        ):
            if other_dim != sharded_dim:
                # shard offset for each shard on the unsharded dimension
                shard_metadata.shard_offsets[other_dim] = 0

    # update global size for ShardedTensorMetadata
    global_size_list = []
    for other_dim in range(
        len(global_sharded_tensor_metadata.shards_metadata[0].shard_sizes)
    ):
        if other_dim != sharded_dim:
            global_size_list.append(
                global_sharded_tensor_metadata.shards_metadata[0].shard_sizes[other_dim]
            )
        else:
            global_size_list.append(cum_sum[-1])
    global_sharded_tensor_metadata.size = torch.Size(global_size_list)