def _local_allgather_into_tensor_coalesced_(
    output_tensors: list[torch.Tensor],
    input_tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    async_op: bool = True,
) -> ScriptObject:
    # "allgather_into_tensor_coalesced_(Tensor[] outputs, Tensor[] inputs, "
    # "__torch__.torch.classes.c10d.ProcessGroup process_group, bool async_op=True) "
    # "-> __torch__.torch.classes.c10d.Work"
    from . import LocalTensor

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    # Each output tensor should be sized to hold all gathered inputs
    # outputs[i] will contain all inputs[i] from all ranks
    if len(output_tensors) != len(input_tensors):
        raise AssertionError(
            f"Number of outputs ({len(output_tensors)}) must match "
            f"number of inputs ({len(input_tensors)})"
        )

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the allgather_into_tensor on them
        group_ranks = [group_offset + r for r in ranks]

        # For each input/output pair
        for input_tensor, output_tensor in zip(input_tensors, output_tensors):
            if not isinstance(input_tensor, LocalTensor):
                raise AssertionError("Input tensor must be a LocalTensor")
            if not isinstance(output_tensor, LocalTensor):
                raise AssertionError("Output tensor must be a LocalTensor")

            if not all(rank in input_tensor._local_tensors for rank in group_ranks):
                continue
            if not all(rank in output_tensor._local_tensors for rank in group_ranks):
                continue

            # Gather input_tensor from all ranks into output_tensor
            # The output should be a concatenation of all inputs along the first dimension
            gathered_tensors = []
            for rank in group_ranks:
                gathered_tensors.append(input_tensor._local_tensors[rank])

            # Concatenate along first dimension and copy to output
            if gathered_tensors:
                concatenated = torch.cat(gathered_tensors, dim=0)
                for rank in group_ranks:
                    output_tensor._local_tensors[rank].copy_(concatenated)

    work = FakeWork()
    work_so = Work.boxed(work)
    return work_so