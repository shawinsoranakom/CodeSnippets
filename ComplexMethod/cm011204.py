def _local_functional_all_to_all_single(
    tensor: torch.Tensor,
    output_split_sizes: list[torch.SymInt],
    input_split_sizes: list[torch.SymInt],
    group_name: GroupName,
) -> torch.Tensor:
    # "all_to_all_single(Tensor input, SymInt[] output_split_sizes, SymInt[] input_split_sizes, str group_name) -> Tensor"
    from . import LocalIntNode, LocalTensor

    ranks, group_offsets, offset = _prepare_collective_groups(
        _resolve_process_group(group_name)
    )

    if not isinstance(tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")

    split_local_sizes: dict[int, list[int]] = {}
    for input_split_size in input_split_sizes:
        if isinstance(input_split_size, torch.SymInt) and isinstance(
            input_split_size.node, LocalIntNode
        ):
            local_ints = dict(input_split_size.node._local_ints.items())
        else:
            local_ints = {rank: int(input_split_size) for rank in tensor._local_tensors}
        for rank, split_size in local_ints.items():
            if rank not in split_local_sizes:
                split_local_sizes[rank] = []
            split_local_sizes[rank].append(split_size)

    split_local_tensors: dict[int, list[torch.Tensor]] = {}

    for rank, split_sizes in split_local_sizes.items():
        split_local_tensors[rank] = list(
            torch.split(tensor._local_tensors[rank], split_sizes)
        )

    output_local_tensors: dict[int, torch.Tensor] = {}

    for group_offset in group_offsets:
        group_ranks = [group_offset + r for r in ranks]

        if not all(rank in split_local_tensors for rank in group_ranks):
            continue

        for i, dst in enumerate(group_ranks):
            splits = []
            for src in group_ranks:
                splits.append(split_local_tensors[src][i])
            output_local_tensors[dst] = torch.cat(splits)

    # pyrefly: ignore [bad-argument-type, bad-argument-count]
    output = LocalTensor(output_local_tensors)

    return output