def _local_reduce_scatter_tensor_coalesced_(
    output_tensors: list[torch.Tensor],
    input_tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    reduce_op_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> ScriptObject:
    # "reduce_scatter_tensor_coalesced_(Tensor[] outputs, Tensor[] inputs, "
    # "__torch__.torch.classes.c10d.ProcessGroup process_group, "
    # "__torch__.torch.classes.c10d.ReduceOp reduce_op, bool async_op=True, "
    # "int timeout=-1) -> __torch__.torch.classes.c10d.Work"

    from . import LocalTensor

    reduce_op = reduce_op_so.op()  # type: ignore[attr-defined]
    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the allreduce on all tensors together
        group_ranks = [group_offset + r for r in ranks]

        # For each tensor, perform the reduction operation
        for input_tensor, output_tensor in zip(input_tensors, output_tensors):
            if not isinstance(input_tensor, LocalTensor):
                raise AssertionError("Input tensor must be a LocalTensor")
            if not isinstance(output_tensor, LocalTensor):
                raise AssertionError("Output tensor must be a LocalTensor")
            if not all(rank in input_tensor._local_tensors for rank in group_ranks):
                continue
            if not all(rank in output_tensor._local_tensors for rank in group_ranks):
                continue

            # Collect tensors from the specified ranks in this group
            group_inputs = []
            for rank in group_ranks:
                group_inputs.append(input_tensor._local_tensors[rank])

            # Perform the reduction operation
            reduced_input = _local_reduce(reduce_op, group_inputs)

            reduced_input_splits = torch.split(
                reduced_input, reduced_input.size(0) // len(group_ranks), dim=0
            )

            # Update all tensors in the group with the reduced result
            for i, rank in enumerate(group_ranks):
                output_tensor._local_tensors[rank].copy_(reduced_input_splits[i])

    work = FakeWork()
    work_so = Work.boxed(work)
    return work_so