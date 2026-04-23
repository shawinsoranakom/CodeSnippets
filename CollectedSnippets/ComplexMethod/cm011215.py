def _local_alltoall_(
    output_tensors: list[torch.Tensor],
    input_tensors: list[torch.Tensor],
    process_group_so: ScriptObject,
    async_op: bool = True,
    timeout: int = -1,
) -> tuple[list[torch.Tensor], ScriptObject]:
    # "alltoall_(Tensor[] output_tensors, Tensor[] input_tensors, "
    # "__torch__.torch.classes.c10d.ProcessGroup process_group, bool async_op=True, "
    # "int timeout=-1) -> (Tensor[], __torch__.torch.classes.c10d.Work)";

    from . import LocalTensor

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    if not (len(input_tensors) == len(output_tensors) == len(ranks)):
        raise AssertionError(
            f"Number of input tensors ({len(input_tensors)}), "
            f"output tensors ({len(output_tensors)}), and ranks ({len(ranks)}) must match"
        )

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the alltoall on them
        group_ranks = [group_offset + r for r in ranks]

        # In alltoall, rank i sends input_tensors[j] to rank j and receives into output_tensors[i] from rank j
        for i, rank_i in enumerate(group_ranks):
            output_tensor = output_tensors[i]
            if not isinstance(output_tensor, LocalTensor):
                raise AssertionError("Output tensor must be a LocalTensor")

            if not all(rank in output_tensor._local_tensors for rank in group_ranks):
                continue

            for j, rank_j in enumerate(group_ranks):
                input_tensor = input_tensors[j]
                if not isinstance(input_tensor, LocalTensor):
                    raise AssertionError("Input tensor must be a LocalTensor")

                if not all(rank in input_tensor._local_tensors for rank in group_ranks):
                    continue

                # Rank i's j-th input tensor goes to rank j's i-th output tensor
                source_tensor = input_tensor._local_tensors[rank_i]
                output_tensor._local_tensors[rank_j].copy_(source_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return (output_tensors, work_so)