def _pre_bucket_all_gather(
    ag_ins: list[torch.Tensor],
    group_size: int,
    group_name: str,
    dtype: torch.dtype,  # type: ignore[name-defined]
    out_dtype_ints: list[
        int
    ],  # dtype enum values, that inputs are converted to before all_gather
    rank: int,
    foreach_group_indices: list[int] | None = None,
) -> torch.Tensor:
    """
    Pre-bucket all gather operation.

    Args:
        ag_ins: Input tensors to gather
        group_size: Size of the process group
        group_name: Name of the process group
        dtype: Target dtype for the bucket
        out_dtype_ints: Dtype enum values for each input
        rank: Current rank
        foreach_group_indices: Optional flat list of grouped indices with -1 as delimiter.
            E.g., [0, 2, -1, 1] means groups [[0, 2], [1]].
    """
    # Convert int indices back to torch.dtype
    out_dtypes = [_ALL_DTYPES[d] for d in out_dtype_ints]
    ins_split_sizes_bytes = [
        ag_in.numel() * out_dtype.itemsize
        for ag_in, out_dtype in zip(ag_ins, out_dtypes, strict=True)
    ]
    bucket_dtype_size_bytes = dtype.itemsize
    ins_split_sizes = [
        _bytes // bucket_dtype_size_bytes for _bytes in ins_split_sizes_bytes
    ]
    ag_input_numel = sum(ins_split_sizes)
    device = ag_ins[0].device
    new_ag_out = torch.empty(ag_input_numel * group_size, dtype=dtype, device=device)
    new_ag_in = new_ag_out.narrow(0, ag_input_numel * rank, ag_input_numel)
    foreach_copy_dsts = torch.split(new_ag_in, ins_split_sizes)
    # View each destination slice as its output dtype, then copy
    # The copy operation handles dtype conversion from input dtype to output dtype
    foreach_copy_dsts_typed = [
        dst.view(out_dtype)
        for dst, out_dtype in zip(foreach_copy_dsts, out_dtypes, strict=True)
    ]
    ag_ins_flattened = [ag_in.reshape(-1) for ag_in in ag_ins]

    # Parse pre-computed groups from flat list with -1 delimiters
    if foreach_group_indices is not None:
        groups_list: list[list[int]] = []
        current_group: list[int] = []
        for idx in foreach_group_indices:
            if idx == -1:
                if current_group:
                    groups_list.append(current_group)
                    current_group = []
            else:
                current_group.append(idx)
        # Add last group if not empty
        if current_group:
            groups_list.append(current_group)

        # Call foreach_copy_ per group
        for group_indices in groups_list:
            group_dsts = [foreach_copy_dsts_typed[idx] for idx in group_indices]
            group_srcs = [ag_ins_flattened[idx] for idx in group_indices]
            torch._foreach_copy_(group_dsts, group_srcs)
    else:
        # No grouping provided - single foreach_copy_ call
        torch._foreach_copy_(foreach_copy_dsts_typed, ag_ins_flattened)
    return new_ag_out