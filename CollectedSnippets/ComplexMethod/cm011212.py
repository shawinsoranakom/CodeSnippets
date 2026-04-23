def _local_all_gather_(
    output_tensors: list[list[torch.Tensor]],
    input_tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[list[list[torch.Tensor]], ScriptObject]:
    # "allgather_(Tensor[][] output_tensors, Tensor[] input_tensors, "
    # "__torch__.torch.classes.c10d.ProcessGroup process_group, bool async_op=True, "
    # "int timeout=-1) -> (Tensor[][], __torch__.torch.classes.c10d.Work)");

    from . import LocalTensor

    if len(output_tensors) != 1:
        raise AssertionError
    if len(input_tensors) != 1:
        raise AssertionError

    input_tensor = input_tensors[0]
    # pyrefly: ignore [bad-assignment]
    output_tensors = output_tensors[0]

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    for i in range(len(output_tensors)):
        if not isinstance(output_tensors[i], LocalTensor):
            raise AssertionError("Output tensor must be a LocalTensor")

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the all_gather on them
        group_ranks = [group_offset + r for r in ranks]

        # For each rank in the group, gather from their input tensor
        for i, rank_i in enumerate(group_ranks):
            # allgather object happens to create pure tensor, so we special case it here
            source_tensor = input_tensor
            if isinstance(input_tensor, LocalTensor):
                source_tensor = input_tensor._local_tensors[rank_i]
            # pyrefly: ignore [missing-attribute]
            output_tensors[i].copy_(source_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    # pyrefly: ignore [bad-return]
    return ([output_tensors], work_so)