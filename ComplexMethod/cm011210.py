def _local_allgather_base_(
    output_tensor: torch.Tensor,
    input_tensor: torch.Tensor,
    process_group_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[torch.Tensor, ScriptObject]:
    # "_allgather_base_(Tensor output_tensor, Tensor input_tensor, __torch__.torch.classes.c10d.ProcessGroup
    # process_group, bool async_op=True, int timeout=-1) -> (Tensor, __torch__.torch.classes.c10d.Work)");
    from . import LocalTensor

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    if not isinstance(output_tensor, LocalTensor):
        raise AssertionError("Output tensor must be a LocalTensor")
    if not isinstance(input_tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")

    for group_offset in group_offsets:
        group_ranks = [group_offset + r for r in ranks]

        if not all(rank in input_tensor._local_tensors for rank in group_ranks):
            continue
        if not all(rank in output_tensor._local_tensors for rank in group_ranks):
            continue

        gathered_tensors = []
        for rank_i in group_ranks:
            gathered_tensors.append(input_tensor._local_tensors[rank_i])

        gathered_tensor = torch.cat(gathered_tensors, dim=0)

        for rank_i in group_ranks:
            output_tensor._local_tensors[rank_i].copy_(gathered_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return output_tensor, work_so