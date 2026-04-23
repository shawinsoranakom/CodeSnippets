def _local_scatter_(
    output_tensors: list[torch.Tensor],
    input_tensors: list[list[torch.Tensor]],
    process_group_so: ScriptObject,
    root_rank: int,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[list[torch.Tensor], ScriptObject]:
    # "scatter_(Tensor[] output_tensors, Tensor[][] input_tensors, "
    # "__torch__.torch.classes.c10d.ProcessGroup process_group, int root_rank, "
    # "bool async_op=True, int timeout=-1) -> (Tensor[], __torch__.torch.classes.c10d.Work)");

    from . import LocalTensor

    if len(output_tensors) != 1:
        raise AssertionError
    if len(input_tensors) != 1:
        raise AssertionError
    output_tensor = output_tensors[0]
    # pyrefly: ignore [bad-assignment]
    input_tensors = input_tensors[0]

    ranks, group_offsets, offset = _prepare_collective_groups(process_group_so)

    # We're going to assume SPMD where for every rank group the root_rank is
    # the same relative to others
    relative_root_rank = root_rank - offset

    if not isinstance(output_tensor, LocalTensor):
        raise AssertionError("Output tensor must be a LocalTensor")
    if len(ranks) != len(input_tensors):
        raise AssertionError((ranks, input_tensors))

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the scatter on them
        group_ranks = [group_offset + r for r in ranks]
        if not all(rank in output_tensor._local_tensors for rank in group_ranks):
            continue

        # Root rank scatters its input tensors to all ranks in this group
        for i, rank in enumerate(group_ranks):
            input_tensor = input_tensors[i]
            if not isinstance(input_tensor, LocalTensor):
                raise AssertionError
            # Each rank i gets the i-th input tensor from the root
            source_tensor = input_tensor._local_tensors[
                group_offset + relative_root_rank
            ]
            output_tensor._local_tensors[rank].copy_(source_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return (output_tensors, work_so)