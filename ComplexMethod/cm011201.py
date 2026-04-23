def _local_functional_all_gather_into_tensor(
    tensor: torch.Tensor, group_size: int, group_name: GroupName
) -> torch.Tensor:
    # "all_gather_into_tensor(Tensor input, int group_size, str group_name) -> Tensor"
    from . import LocalTensor

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

        gathered_tensor = torch.cat(group_tensors, dim=0)

        for rank in group_ranks:
            output_local_tensors[rank] = gathered_tensor.clone()

    # pyrefly: ignore [bad-argument-type, bad-argument-count]
    output = LocalTensor(output_local_tensors)

    return output