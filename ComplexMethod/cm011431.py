def _get_shard_size_and_offsets(
    curr_local_size: int,
    mesh_dim_size: int,
    rank: RankType,
    placement: Shard | _StridedShard,
    previous_offsets,
    zero_global_offset: int,
    skip_offset: bool,
) -> tuple[int, torch.Tensor | None]:
    kwargs: dict[str, Any] = {
        "curr_local_size": curr_local_size,
        "num_chunks": mesh_dim_size,
        "rank": rank,
    }
    if isinstance(placement, _StridedShard):
        kwargs["return_first_offset"] = False
    shard_size, shard_offsets = placement._local_shard_size_and_offset(**kwargs)
    if skip_offset:
        return shard_size, None
    if shard_size == 0:
        return shard_size, torch.arange(zero_global_offset, zero_global_offset + 1)
    if isinstance(placement, Shard) and not isinstance(placement, _StridedShard):
        if not isinstance(shard_offsets, int):
            raise AssertionError
        index = torch.arange(shard_offsets, shard_offsets + shard_size)
    else:
        if not isinstance(shard_offsets, list):
            raise AssertionError
        index = torch.tensor(shard_offsets)
    if previous_offsets is None:
        return shard_size, index
    else:
        return shard_size, previous_offsets[index]