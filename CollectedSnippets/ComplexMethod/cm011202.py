def _local_functional_reduce_scatter_tensor(
    tensor: torch.Tensor, reduce_op: str, group_size: int, group_name: GroupName
) -> torch.Tensor:
    #  "reduce_scatter_tensor(Tensor input, str reduce_op, int group_size, str group_name) -> Tensor"
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

        reduced_tensor = _local_reduce(reduce_op, group_tensors)

        scattered_tensor = torch.split(
            reduced_tensor,
            reduced_tensor.size(0) // len(group_ranks),
            dim=0,
        )

        for i, rank in enumerate(group_ranks):
            if i < len(scattered_tensor):
                output_local_tensors[rank] = scattered_tensor[i].clone()
            else:
                output_local_tensors[rank] = _zero_sized_like(reduced_tensor, 0)

    # pyrefly: ignore [bad-argument-type, bad-argument-count]
    output = LocalTensor(output_local_tensors)

    return output