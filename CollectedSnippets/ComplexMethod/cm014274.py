def group_tensors_by_device_and_dtype(
    tensorlistlist: list[list[torch.Tensor | None]], with_indices: bool = False
) -> dict[tuple[torch.device, torch.dtype], tuple[list[list[Any]], list[int]]]:
    """Pure Python implementation of torch._C._group_tensors_by_device_and_dtype.

    Groups tensors by their device and dtype. This is useful before sending
    tensors off to a foreach implementation, which requires tensors to be on
    one device and dtype.

    Args:
        tensorlistlist: A list of lists of tensors (tensors can be None).
        with_indices: If True, track original indices in the output.

    Returns:
        A dict mapping (device, dtype) tuples to (grouped_tensorlistlist, indices).
    """
    # Result dict: (device, dtype) -> (list of lists, indices)
    result: dict[
        tuple[torch.device, torch.dtype], tuple[list[list[Any]], list[int]]
    ] = {}

    if not tensorlistlist or not tensorlistlist[0]:
        return result

    num_lists = len(tensorlistlist)
    num_tensors = len(tensorlistlist[0])

    for idx in range(num_tensors):
        # Find the first non-None tensor at this index to get device and dtype
        first_tensor = None
        for tlist in tensorlistlist:
            if tlist is not None and idx < len(tlist) and tlist[idx] is not None:
                first_tensor = tlist[idx]
                break

        if first_tensor is None:
            # All tensors at this index are None, skip
            continue

        key = (first_tensor.device, first_tensor.dtype)

        if key not in result:
            # Initialize empty lists for each tensorlist
            result[key] = ([[] for _ in range(num_lists)], [])

        grouped_lists, indices = result[key]

        # Add tensors from each list at this index
        for list_idx, tlist in enumerate(tensorlistlist):
            if tlist is not None and idx < len(tlist):
                grouped_lists[list_idx].append(tlist[idx])
            else:
                grouped_lists[list_idx].append(None)

        if with_indices:
            indices.append(idx)

    return result