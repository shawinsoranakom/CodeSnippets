def _local_reduce_scatter_base_(  # type: ignore[no-untyped-def]
    output_tensor: torch.Tensor,
    input_tensor: torch.Tensor,
    process_group_so: ScriptObject,
    reduce_op_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[torch.Tensor, ScriptObject]:
    # "_reduce_scatter_base_(Tensor output_tensor, Tensor input_tensor,
    # __torch__.torch.classes.c10d.ProcessGroup process_group, __torch__.torch.classes.c10d.ReduceOp reduce_op,
    # bool async_op=True, int timeout=-1) -> (Tensor, __torch__.torch.classes.c10d.Work)"

    from . import LocalTensor

    reduce_op = reduce_op_so.op()  # type: ignore[attr-defined]
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

        reduced_tensor = _local_reduce(reduce_op, gathered_tensors)

        scattered_tensor = torch.split(
            reduced_tensor,
            reduced_tensor.size(0) // len(group_ranks),
            dim=0,
        )

        for i, rank_i in enumerate(group_ranks):
            output_tensor._local_tensors[rank_i].copy_(scattered_tensor[i].clone())

    work = FakeWork()
    work_so = Work.boxed(work)
    return output_tensor, work_so