def all_gather_inplace(
    tensor_list: list[torch.Tensor],
    tensor: torch.Tensor,
    group=None,
    async_op=False,
    tag: str = "",
):
    if async_op:
        raise AssertionError(
            "Can't remap async version of inplace op to functional collective"
        )
    if tensor.dim() != 0 and not all(t.size(0) == tensor.size(0) for t in tensor_list):
        raise AssertionError("Remapping variable size all_gather is not yet supported")

    group = group or dist.group.WORLD
    if group is None:
        raise AssertionError("group cannot be None")

    output = all_gather_tensor(tensor, 0, group, tag)

    # Use aten.slice instead of aten.split because the latter causes
    # tensor.shape(0) to be unnecessarily baked in when it's a SymInt.
    output_splits = []
    offset = 0
    for t in tensor_list:
        is_scalar = t.dim() == 0
        t_offset = 1 if is_scalar else t.size(0)

        out = output[offset] if is_scalar else output[offset : offset + t_offset]
        output_splits.append(out)

        offset += t_offset
    for dst, src in zip(tensor_list, output_splits):
        dst.copy_(src)
    return tensor_list