def _local_allreduce_coalesced_(
    tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    reduce_op_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> ScriptObject:
    # "allreduce_coalesced_(Tensor[] tensors, __torch__.torch.classes.c10d.ProcessGroup process_group, "
    # "__torch__.torch.classes.c10d.ReduceOp reduce_op, bool async_op=True, int timeout=-1) -> __torch__.torch.classes.c10d.Work"
    from . import LocalTensor

    reduce_op = reduce_op_so.op()  # type: ignore[attr-defined]
    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the allreduce on all tensors together
        group_ranks = [group_offset + r for r in ranks]

        # For each tensor, perform the reduction operation
        for tensor in tensors:
            if not isinstance(tensor, LocalTensor):
                raise AssertionError("Input tensor must be a LocalTensor")
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
    return work_so