def _local_functional_shard_dim_alltoall(
    tensor: torch.Tensor, gather_dim: int, shard_dim: int, group_name: GroupName
) -> torch.Tensor:
    # "shard_dim_alltoall(Tensor input, int gather_dim, int shard_dim, str group_name) -> Tensor"
    from . import _zero_sized_like, LocalTensor

    ranks, group_offsets, offset = _prepare_collective_groups(
        _resolve_process_group(group_name)
    )

    if not isinstance(tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")
    output_local_tensors: dict[int, torch.Tensor] = {}

    for group_offset in group_offsets:
        group_ranks = [group_offset + r for r in ranks]

        group_tensors = []
        if not all(rank in tensor._local_tensors for rank in group_ranks):
            continue

        for rank in group_ranks:
            group_tensors.append(tensor._local_tensors[rank])

        gathered_tensor = torch.cat(group_tensors, dim=gather_dim)

        split_tensor = torch.split(
            gathered_tensor,
            gathered_tensor.size(shard_dim) // len(group_ranks),
            dim=shard_dim,
        )

        for i, rank in enumerate(group_ranks):
            if i < len(split_tensor):
                output_local_tensors[rank] = split_tensor[i].clone()
            else:
                output_local_tensors[rank] = _zero_sized_like(
                    gathered_tensor, shard_dim
                )

    # pyrefly: ignore [bad-argument-type, bad-argument-count]
    output = LocalTensor(output_local_tensors)

    return output