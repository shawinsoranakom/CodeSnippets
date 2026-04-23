def _local_alltoall_base_(
    output_tensor: torch.Tensor,
    input_tensor: torch.Tensor,
    process_group_so: ScriptObject,
    output_split_sizes: list[int],
    input_split_sizes: list[int],
    async_op: bool = True,
    timeout: int = -1,
) -> ScriptObject:
    # "alltoall_base_(Tensor output, Tensor input, __torch__.torch.classes.c10d.ProcessGroup process_group, "
    # "int[] output_split_sizes, int[] input_split_sizes, bool async_op=True, int timeout=-1) -> __torch__.torch.classes.c10d.Work";

    from . import LocalTensor

    ranks, group_offsets, _offset = _prepare_collective_groups(process_group_so)

    if not isinstance(input_tensor, LocalTensor):
        raise AssertionError("Input tensor must be a LocalTensor")
    if not isinstance(output_tensor, LocalTensor):
        raise AssertionError("Output tensor must be a LocalTensor")
    # Convert split sizes to lists if they aren't already
    if output_split_sizes is not None:
        output_split_sizes = list(output_split_sizes)
    if input_split_sizes is not None:
        input_split_sizes = list(input_split_sizes)

    for group_offset in group_offsets:
        # For the tensors in this group [group_offset + r for r in ranks]
        # perform the alltoall_base on them
        group_ranks = [group_offset + r for r in ranks]

        if not all(rank in input_tensor._local_tensors for rank in group_ranks):
            continue
        if not all(rank in output_tensor._local_tensors for rank in group_ranks):
            continue

        for i, rank_i in enumerate(group_ranks):
            # Split input tensor from rank_i according to input_split_sizes
            rank_tensor = input_tensor._local_tensors[rank_i]

            if input_split_sizes is not None and len(input_split_sizes) > 0:
                # Split the input tensor
                input_splits = torch.split(rank_tensor, input_split_sizes, dim=0)
            else:
                # No split sizes specified, split evenly
                split_size = rank_tensor.size(0) // len(group_ranks)
                input_splits = torch.split(rank_tensor, split_size, dim=0)

            # Send each split to the corresponding rank
            for j, rank_j in enumerate(group_ranks):
                if j < len(input_splits):
                    split_tensor = input_splits[j]

                    # Determine where to place this split in the output tensor
                    if output_split_sizes is not None and len(output_split_sizes) > 0:
                        # Calculate offset based on output split sizes
                        output_offset = sum(output_split_sizes[:i]) if i > 0 else 0
                        end_offset = (
                            output_offset + output_split_sizes[i]
                            if i < len(output_split_sizes)
                            else output_tensor._local_tensors[rank_j].size(0)
                        )
                    else:
                        # No output split sizes, use even splits
                        split_size = output_tensor._local_tensors[rank_j].size(
                            0
                        ) // len(group_ranks)
                        output_offset = i * split_size
                        end_offset = min(
                            (i + 1) * split_size,
                            output_tensor._local_tensors[rank_j].size(0),
                        )

                    # Copy the split to the appropriate section of the output tensor
                    output_section = output_tensor._local_tensors[rank_j][
                        output_offset:end_offset
                    ]
                    if output_section.numel() > 0:
                        # Reshape split_tensor to match output_section if necessary
                        if split_tensor.size() != output_section.size():
                            split_tensor = split_tensor.view(output_section.size())
                        output_section.copy_(split_tensor)

    work = FakeWork()
    work_so = Work.boxed(work)
    return work_so