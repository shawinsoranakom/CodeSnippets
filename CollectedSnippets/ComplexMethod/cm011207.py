def _local_all_reduce_(
    tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    reduce_op_so: ScriptObject,
    sparse_indices: torch.Tensor | None = None,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[list[torch.Tensor], ScriptObject]:
    # "allreduce_(Tensor[] tensors, __torch__.torch.classes.c10d.ProcessGroup process_group, "
    # "__torch__.torch.classes.c10d.ReduceOp reduce_op, Tensor? sparse_indices, bool async_op=True, "
    # "int timeout=-1) -> (Tensor[], __torch__.torch.classes.c10d.Work)");
    from . import LocalTensor

    if len(tensors) != 1:
        raise AssertionError
    tensor = tensors[0]
    reduce_op = reduce_op_so.op()  # type: ignore[attr-defined]

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    if not isinstance(tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the allreduce on them
        group_ranks = [group_offset + r for r in ranks]
        if not all(rank in tensor._local_tensors for rank in group_ranks):
            continue

        # Collect tensors from the specified ranks in this group
        group_tensors = []
        for rank in group_ranks:
            group_tensors.append(tensor._local_tensors[rank])

        # Perform the reduction operation
        reduced_tensor = _local_reduce(reduce_op, group_tensors)

        # Update all tensors in the group with the reduced result
        for rank in group_ranks:
            tensor._local_tensors[rank].copy_(reduced_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return (tensors, work_so)