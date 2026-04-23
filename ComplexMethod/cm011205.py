def _local_broadcast_(
    tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    root_rank: int,
    root_tensor: int,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[list[torch.Tensor], ScriptObject]:
    # "broadcast_(Tensor[] tensors, __torch__.torch.classes.c10d.ProcessGroup process_group, "
    # "int root_rank, int root_tensor, bool async_op=True, int timeout=-1) -> (Tensor[], __torch__.torch.classes.c10d.Work)"
    from . import LocalTensor

    if len(tensors) != 1:
        raise AssertionError
    if root_tensor != 0:
        raise AssertionError
    tensor = tensors[0]

    ranks, group_offsets, offset = _prepare_collective_groups(process_group_so)

    # We're going to assume SPMD where for every rank group the root_rank is
    # the same relative to others
    relative_root_rank = root_rank - offset

    if not isinstance(tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the broadcast on them
        group_ranks = [group_offset + r for r in ranks]
        if not all(rank in tensor._local_tensors for rank in group_ranks):
            continue

        source_rank = group_offset + relative_root_rank
        source_tensor = tensor._local_tensors[source_rank]

        # Broadcast the source tensor to all ranks in this group
        for rank in group_ranks:
            if source_rank != rank:
                tensor._local_tensors[rank].copy_(source_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return (tensors, work_so)