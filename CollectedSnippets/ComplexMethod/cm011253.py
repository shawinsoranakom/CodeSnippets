def reshard_local_shard(
    local_tensor: torch.Tensor,
    st_size: torch.Size,
    sharding_spec: shard_spec.ShardingSpec,
    resharding_spec: shard_spec.ShardingSpec,
    pg: ProcessGroup,
) -> tuple[list[Shard], list[ShardMetadata]]:
    """
    Reshard a sharded tensor given the ``resharding_spec``. When the reshard dim is
    different from the original sharding dim, we need to do two steps logically:
    1. To collect all shards based on original sharding spec.
    2. Reshard the tensor based on the given resharding spec.

    In reality, we consolidate the two steps into one by sending each rank the new
    shard based on the resharding spec.

    Args:
        local_tensor (Tensor): Local tensor stored in the current rank.
        st_size (torch.Size): The size of the sharded tensor.
        sharding_spec (:class:`torch.distributed._shard.sharding_spec.ShardingSpec`): The
            specification describing how the tensor is sharded originally.
        resharding_spec (:class:`torch.distributed._shard.sharding_spec.ShardingSpec`): The
            specification describing how the tensor will be resharded.
        pg (ProcessGroup): The process group to aggregate on.

    Returns:
        A Tuple of the followings:
            A List[`Shard`] which contains the local tensor and its metadata.
            A List[`ShardMetadata`] which contains the metadata for the shard, including
                offsets, lengths and device placement.
    """
    current_rank = dist.get_rank(pg)
    world_size = dist.get_world_size(pg)
    current_sharding_dim = int(sharding_spec.dim)  # type: ignore[attr-defined]
    reshard_dim = int(resharding_spec.dim)  # type: ignore[attr-defined]

    # Build shards_metadata first.
    shards_metadata, ranks = build_reshard_metadata(
        st_size, resharding_spec, world_size
    )

    # Compute expected size
    input_split_sizes = [
        metadata.shard_sizes[reshard_dim] for metadata in shards_metadata
    ]
    rearrange_input = any(ranks[i] > ranks[i + 1] for i in range(len(ranks) - 1))

    if rearrange_input:
        # Need to re-arrange reshard_dim of local_tensor before all2all.
        indices: list[int] = []
        for metadata in shards_metadata:
            offset_start_idx = metadata.shard_offsets[reshard_dim]
            split_size = metadata.shard_sizes[reshard_dim]
            indices += range(offset_start_idx, offset_start_idx + split_size)
        local_tensor = local_tensor.index_select(
            reshard_dim, torch.tensor(indices, device=local_tensor.device)
        )

    # Because reshard_dim != original shard_dim. We need to compute the
    # size of tensor from each rank.
    output_tensor_list = [torch.tensor(1)] * world_size
    split_size = get_split_size(st_size[current_sharding_dim], world_size)
    rearrange_output_list = False
    indices = []
    for idx, placement in enumerate(sharding_spec.placements):  # type: ignore[attr-defined]
        sharded_dim_size = get_chunked_dim_size(
            st_size[current_sharding_dim], split_size, idx
        )
        output_tensor_size = list(st_size)
        output_tensor_size[current_sharding_dim] = sharded_dim_size
        output_tensor_size[reshard_dim] = input_split_sizes[current_rank]
        output_tensor_list[placement.rank()] = torch.empty(  # type: ignore[union-attr, index]
            output_tensor_size, device=local_tensor.device, dtype=local_tensor.dtype
        )
        indices.append(placement.rank())  # type: ignore[union-attr, index, arg-type]
        if idx != placement.rank():  # type: ignore[union-attr]
            rearrange_output_list = True

    # Perform autograd enabled all2all.
    input_tensor_tuple = torch.split(local_tensor, input_split_sizes, dim=reshard_dim)
    input_tensor_list = [tensor.contiguous() for tensor in input_tensor_tuple]
    output_tensor_list = all_to_all(
        output_tensor_list,
        input_tensor_list,
        group=pg,
    )

    if rearrange_output_list:
        # Need to re-arrange original shard_dim of output_tensor_list.
        output_tensor_list = [output_tensor_list[idx] for idx in indices]  # type: ignore[call-overload]
    local_tensor = torch.cat(output_tensor_list, dim=current_sharding_dim)
    local_shards = [Shard(local_tensor, shards_metadata[current_rank])]
    return local_shards, shards_metadata