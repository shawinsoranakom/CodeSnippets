def build_metadata_from_local_shards(
    local_shards: list[Shard],
    global_size: torch.Size,
    current_rank: int,
    pg: c10d.ProcessGroup,
) -> ShardedTensorMetadata:
    if len(local_shards) <= 0:
        raise AssertionError("must have local shards!")
    local_shard_metadatas: list[ShardMetadata] = []

    first_shard_dtype = local_shards[0].tensor.dtype
    first_shard_layout = local_shards[0].tensor.layout
    first_shard_requires_grad = local_shards[0].tensor.requires_grad
    first_shard_is_pinned = local_shards[0].tensor.is_pinned()

    # 1). Validate local tensors and associated metadatas
    for local_shard in local_shards:
        local_shard_tensor = local_shard.tensor
        local_shard_meta = local_shard.metadata
        local_shard_metadatas.append(local_shard_meta)
        rank, local_device = _parse_and_validate_remote_device(
            pg, local_shard_meta.placement
        )

        if (
            local_shard_tensor.layout != torch.strided
            or local_shard_tensor.layout != first_shard_layout
        ):
            raise ValueError(
                f"Only torch.strided layout is currently supported, but found "
                f"{local_shard_tensor.layout} on rank:{current_rank}!"
            )

        if not local_shard_tensor.is_contiguous():
            raise ValueError(
                "Only torch.contiguous_format memory_format is currently supported!"
            )

        if rank != current_rank:
            raise ValueError(
                f"Local shard metadata's rank does not match with the rank in its process group! "
                f"Found current rank in the process group: {current_rank}, "
                f"local ShardMetadata placement's rank: {rank}"
            )
        if local_shard_tensor.device != local_device:
            raise ValueError(
                f"Local shard tensor device does not match with local Shard's placement! "
                f"Found local shard tensor device: {local_shard_tensor.device}, "
                f"local shard metadata placement device: {local_device}"
            )

        _raise_if_mismatch(
            local_shard_meta.shard_sizes,
            list(local_shard_tensor.size()),
            "size",
            current_rank,
        )
        _raise_if_mismatch(
            local_shard_tensor.is_pinned(),
            first_shard_is_pinned,
            "pin_memory",
            current_rank,
        )
        _raise_if_mismatch(
            local_shard_tensor.dtype, first_shard_dtype, "dtype", current_rank
        )
        _raise_if_mismatch(
            local_shard_tensor.requires_grad,
            first_shard_requires_grad,
            "requires_grad",
            current_rank,
        )

    # 2). Build a "local" ShardedTensorMetadata with all local shards on this rank, then
    #    do all_gather to collect local_sharded_tensor_metadata from all ranks
    local_tensor_properties = TensorProperties(
        dtype=first_shard_dtype,
        layout=first_shard_layout,
        requires_grad=first_shard_requires_grad,
        memory_format=torch.contiguous_format,
        pin_memory=first_shard_is_pinned,
    )

    local_sharded_tensor_metadata = ShardedTensorMetadata(
        shards_metadata=local_shard_metadatas,
        size=global_size,
        tensor_properties=local_tensor_properties,
    )

    return local_sharded_tensor_metadata